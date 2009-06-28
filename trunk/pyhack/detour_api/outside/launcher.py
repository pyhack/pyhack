import os
import sys
import logging
import pickle

log = logging.getLogger(__name__)

from util.defines import *
from detour_api.outside.process import Process

from util.paths import Paths

class TargetLaunchException(Exception):
	def __init__(self, retVal, message):
		super(TargetLaunchException, self).__init__(retVal, message)
		self.message = message

class TargetLauncher(object):
	CREATION_PAUSE = 1
	ALLOC_ALLOCATED = 2
	REMOTE_THREAD_RETURN = 3
	ALLOC_BEFORE_FREE = 4

	def __init__(self, dll, pyHome, targetDef):
		self.dll = dll
		self.pyHome = pyHome
		self.targetDef = targetDef
	
	@staticmethod
	def _enableDebugPrivilege():
		log.debug("Enabling SeDebugPrivilege")
		Process().token.enableDebugPrivilege()
	
	def _launcher_environ_config(self):
		#Add path to pyHome so CreateProcess() can find python26_d
		
		p = os.environ['PATH'].split(";")
		p.append(self.pyHome) #need to add path to python so 
		os.environ['PATH'] = ';'.join(p)
		
		conf = {
			'dll': self.dll,
			'pyHome': self.pyHome,
			'targetDef': self.targetDef,
		}
		os.environ['pyHack_Path'] = Paths.pyHack
		os.environ['pyHack_ParentPath'] = Paths.trunk
		os.environ['pyHack_DLLPath'] = os.path.dirname(Paths.get_dll_path())
		os.environ['pyHack_Config'] = pickle.dumps(conf)

	def launch(self):
		"""A simplified interface for _launch_process that assumes the launch is happening via a CLI"""
		for step, args in self.launch_process():
			if step == TargetLauncher.CREATION_PAUSE:
				p = args[0]
				#log.info("Attach debugger now, and press enter to continue")
				#raw_input()
			if step == TargetLauncher.REMOTE_THREAD_RETURN:
				retVal = args[0]
				
		log.info("Remote thread return value: %d"%(retVal))
		if retVal == 0:
			return p
		e = "Scary Unknown Error in remote thread (%s)"%(retVal)
		if retVal == 1:
			e = "Remote thread failed LoadLibrary()"
		if retVal == 2:
			e = "Remote thread failed GetProcAddress() for dll function"
		if retVal == 3:
			e = "Remote python function failed reading python file"
		if retVal == 4:
			e = "Remote python function encountered an exception in python file"
		if retVal == 3221225786:
			e = "Remote console window closed or other scary error"
		log.error(e)
		raise TargetLaunchException(retVal, e)
		return retVal
		
	def launch_process(self):
		"""This function is a generator. Each time it is resumed, another step in launching the process occurs."""
		
		targetDef = self.targetDef

		self._enableDebugPrivilege()

		self._launcher_environ_config()

		p = Process.create(targetDef.exe, targetDef.args, targetDef.startIn, suspended=True)
		log.info("Spawned target, pid %d, main thread id %s"%(p.pid, p._idMainThread))
		
		yield (TargetLauncher.CREATION_PAUSE, (p, ))

		log.info("Creating injection stub")
		alloc = self._createInjectedStub(self.dll, targetDef, p.memory)

		yield (TargetLauncher.ALLOC_ALLOCATED, (alloc, ))
		
		log.info("Creating remote thread")
		retVal = p.createRemoteThreadWait(alloc['executionPoint']+1)
		
		yield (TargetLauncher.REMOTE_THREAD_RETURN, (retVal, ))
		
		yield (TargetLauncher.ALLOC_BEFORE_FREE, (alloc, ))
		
		log.info("Freeing memory")
		for a in alloc.values():
			p.memory.free(a)


	def _createInjectedStub(self, dll, targetDef, mem):
		alloc = {}
		#alloc['pyPath'] = mem.allocWrite(targetDef.pycode)
		alloc['pyPath'] = mem.allocWrite(Paths.inside_bootstrap_py)
		alloc['dllPath'] = mem.allocWrite(dll)
		alloc['dllFunc'] = mem.allocWrite("run_python_file")
		alloc['executionPoint'] = mem.alloc(None, 128) #we need about 45 bytes
		hM = kernel32.GetModuleHandleA("kernel32.dll")

		from util.buffer import ASMBuffer
		buf = ASMBuffer(128)

		buf.INT3() #Debugger trap
		
		buf.movEAX_Addr(kernel32.GetProcAddress(hM, "AllocConsole"))
		buf.callEAX() #AllocConsole() address -> EAX
		
		buf.pushAddr(alloc['dllPath'])
		buf.movEAX_Addr(kernel32.GetProcAddress(hM, "LoadLibraryA"))
		buf.callEAX() #hModule to dll -> EAX

		buf.cmpEAX_Byte(0x0)
		buf.namedJNZ("ll_success")

		if True:
			buf.pushByte(1) #PUSH 0x1 (thread exit code) 1 = LoadLibrary Failed
			buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
			buf.callEAX() #This cleanly exits the thread	

		buf.nameTarget("ll_success")
		buf.pushAddr(alloc['dllFunc'])
		buf.pushEAX()	#PUSH EAX (hModule to dll)
		buf.movEAX_Addr(kernel32.GetProcAddress(hM, "GetProcAddress"))
		buf.callEAX() #dllFunc() address -> EAX

		buf.cmpEAX_Byte(0x0)
		buf.namedJNZ("gpa_success")

		if True:
			buf.pushByte(2) #PUSH 0x2 (thread exit code) 2 = GetProcAddress Failed
			buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
			buf.callEAX() #This cleanly exits the thread

		buf.nameTarget("gpa_success")
		buf.pushAddr(1) #turns on pdb debugging
		buf.pushAddr(alloc['pyPath'])
		buf.callEAX() #This calls our run_python_code script
		buf.addESP(8)
		buf.cmpEAX_Byte(0x0)
		buf.namedJZ("run_success")

		if True:
			buf.addEAX(2) #increase the func's error code to accomodate for this stub's error code
			buf.pushEAX()
			buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
			buf.callEAX() #This cleanly exits the thread
		
		buf.nameTarget("run_success")
		
		
		
		
		
		#buf.INT3()
		
		buf.pushByte(0) #PUSH 0x0 (thread exit code)
		buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
		buf.callEAX() #This cleanly exits the thread
		
		
		buf.push([0xCC, 0xCC, 0xCC, 0xCC, 0xCC]) #Debugger trap
		buf.push([0xCC, 0xCC, 0xCC, 0xCC, 0xCC]) #Debugger trap
		
		mem.write(alloc['executionPoint'], buf.buf.raw)
		
		return alloc