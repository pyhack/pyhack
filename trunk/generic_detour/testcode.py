import sys
import ctypes
import detour

print "test.py loaded"

def myCallback(*args, **kwargs):
	detouraddr, registers, flags, caller = args[0], args[1], args[2], args[3]

	x = """Detour Address: 0x%08x
Registers: 
	EAX: 0x%08x
	ECX: 0x%08x
	EDX: 0x%08x
	EBX: 0x%08x
	ESP: 0x%08x
	EBP: 0x%08x
	ESI: 0x%08x
	EDI: 0x%08x
Flags: 0x%08x
Caller: 0x%08x"""%(
	detouraddr, 
	registers[0], 
	registers[1], 
	registers[2], 
	registers[3], 
	registers[4], 
	registers[5], 
	registers[6], 
	registers[7], 
	flags, 
	caller)
        print x

detour.callback = myCallback
