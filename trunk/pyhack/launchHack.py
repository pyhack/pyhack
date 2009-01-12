"""
This file is run outside of the process as a launcher.
It's purpose is to decide what application to inject into, and app is associated with it.
"""
import sys
import logging
from util.defines import *
from util.process import Process


targets = {
	'randomNumber': {
		'exe': r"Z:\testApp\Release\randomNumber.exe",
		'startIn': r"Z:\testApp\Release",
		'args': r"",
		'pycode': r"Z:\pyhack\trunk\toolkit\randomNumber.py",
	}
}

logging.basicConfig(
	level=logging.DEBUG,
	datefmt='%Y-%m-%d %H:%M:%S',
	format="%(asctime)-15s %(levelname)-8s %(name)s %(funcName)s: %(message)s",
)
log = logging.getLogger()

def main(argv):
	dll = r"Z:\pyhack\trunk\toolkit\Debug\pydetour_d.pyd"
	targetName = 'randomNumber'
	
	log.info("Initializing launchHack.py.")
	log.info("Selected target: %s"%(targetName))
	log.debug("Target DLL: %s"%(dll))
	
	targetDef = targets[targetName]
	
	log.debug("Enabling SeDebugPrivilege")
	Process().token.enableDebugPrivilege()
	
	
	p = Process.create(targetDef['exe'], targetDef['args'], targetDef['startIn'], suspended=True)
	print p.pid

	def crt():
		alloc = createInjectedStub(dll, targetDef, p.memory)
		print p.createRemoteThreadWait(alloc['executionPoint']+1)
	
	import code
	code.interact(banner="", local=locals())

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
		buf.pushByte(2) #PUSH 0x1 (thread exit code) 2 = GetProcAddress Failed
		buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
		buf.callEAX() #This cleanly exits the thread	

	buf.nameTarget("gpa_success")
	buf.movEAX_Addr(alloc['pyPath'])
	buf.callEAX() #This calls our run_python_code script


	buf.pushByte(0) #PUSH 0x0 (thread exit code)
	buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
	buf.callEAX() #This cleanly exits the thread
	
	
	buf.push([0xCC, 0xCC, 0xCC, 0xCC, 0xCC]) #Debugger trap
	buf.push([0xCC, 0xCC, 0xCC, 0xCC, 0xCC]) #Debugger trap
	
	mem.write(alloc['executionPoint'], buf.buf.raw)
	
	return alloc

if __name__ == '__main__':
	main(sys.argv)
