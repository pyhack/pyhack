"""
This file is run outside of the process as a launcher.
It's purpose is to decide what application to inject into, and app is associated with it.
"""
import sys
import os
import logging
from util.defines import *
from util.process import Process

import pickle

targets = {
	'randomNumber': {
		'exe': r"Z:\pyhack\testApps\randomNumber\Release\randomNumber.exe",

		'startIn': r"Z:\pyhack\testApps\randomNumber\Release",
		'args': r"",
		'pycode': r"Z:\pyhack\trunk\pyhack\apps\randomNumber.py",
	}
	
}

logging.basicConfig(
	level=logging.DEBUG,
	datefmt='%Y-%m-%d %H:%M:%S',
	format="%(asctime)-15s %(levelname)-8s %(name)s %(funcName)s: %(message)s",
)
log = logging.getLogger()

def main(argv):
	targetName = argv[1]
	targetDef = targets[targetName]	
	conf = {
		'dll': r"Z:\pyhack\trunk\toolkit\Debug\pydetour_d.pyd",
		'pyHome': r"Z:\pyhack\python",
		'targetName': targetName,
		'targetDef': targetDef,
	}
	
	log.info("Initializing launchHack.py.")
	log.info("Selected target: %s"%(targetName))
	log.debug("Target DLL: %s"%(conf['dll']))
	
	
	
	log.debug("Enabling SeDebugPrivilege")
	Process().token.enableDebugPrivilege()
	
	os.environ['pyDetourConfig'] = pickle.dumps(conf)
	p = os.environ['PATH'].split(";")
	p.append(conf['pyHome']) #need to add path to python to python26_d can get loaded during CreateProcess()
	os.environ['PATH'] = ';'.join(p)
	
	p = Process.create(targetDef['exe'], targetDef['args'], targetDef['startIn'], suspended=True)
	log.info("Spawned target, pid %d, main thread id %s"%(p.pid, p._idMainThread))
	
	log.info("Attach debugger now, and press enter to continue")
	raw_input()

	log.info("Creating injection stub")
	alloc = createInjectedStub(conf['dll'], targetDef, p.memory)
	log.info("Creating remote thread")
	retVal = p.createRemoteThreadWait(alloc['executionPoint']+1)
	log.info("Remote thread return value: %d"%(retVal))
	if retVal == 1:
		log.error("Remote thread failed LoadLibrary()")
	if retVal == 2:
		log.error("Remote thread failed GetProcAddress() for dll function")
	if retVal == 3:
		log.error("Remote python function failed reading python file")
	if retVal == 4:
		log.error("Remote python function encountered an exception in python file")
	log.info("Freeing memory")
	for a in alloc.values():
		p.memory.free(a)
	if retVal == 0:
		log.info("Resuming main thread")
		p.resume()
	#import code
	#code.interact(banner="", local=locals())

def createInjectedStub(dll, targetDef, mem):
	alloc = {}
	alloc['pyPath'] = mem.allocWrite(targetDef['pycode'])
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

if __name__ == '__main__':
	main(sys.argv)
