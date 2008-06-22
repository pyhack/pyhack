import sys
import ctypes
import detour

print "test.py loaded"

class register_list:
	def __init__(self, registertuple, flags):
		self.eax = registertuple[0]
		self.ecx = registertuple[1]
		self.edx = registertuple[2]
		self.ebx = registertuple[3]
		self.esp = registertuple[4]
		self.ebp = registertuple[5]
		self.esi = registertuple[6]
		self.edi = registertuple[7]
		self.flags = flags
	def __str__(self):
		return "(EAX: 0x%08x, ECX: 0x%08x, EDX: 0x%08x, EBX: 0x%08x, ESP: 0x%08x, EBP: 0x%08x, ESI: 0x%08x, EDI: 0x%08x, flags: 0x%08x)"%(self.eax, self.ecx, self.edx, self.ebx, self.esp, self.ebp, self.esi, self.edi, self.flags)


def myCallback(*args, **kwargs):
	detouraddr, r, flags, caller = args[0], args[1], args[2], args[3]
	registers = register_list(r, flags)

	x = """Detour Address: 0x%08x
Caller: 0x%08x
Registers: %s
"""%(
	detouraddr, 
	caller,
	registers, 
)
        print x

detour.callback = myCallback
