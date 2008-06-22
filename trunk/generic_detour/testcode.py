import gdetour

print "testcode.py loaded"

##############################################################
##############################################################
##############################################################
#	Everything in this section should be regarded as API
##############################################################
##############################################################
##############################################################

class register_list:
	"""Helpful register_list class. Holds the 8 main registers and the flags register"""
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

class pyDetourConfig:
	"""Configuration of a gdetour that can be changed throughout the detour's lifetime"""
	def __init__(self, addr):
		self.address = addr
		self.callback = None

class callback_obj:
	"""This is the object passed to function that are registed as callbacks. It should be the only way to interact with gdetour"""

	def __init__(self, address, registers, caller):
		self.address = address	
		self.registers = registers
		self.caller = caller

	@staticmethod
	def read(address, length):
		return gdetour.read(address, length)

	@staticmethod
	def write(address, length):
		return gdetour.write(address, length)

	def dump(self):
		print "Dump for call to 0x%08x from 0x%08x:"%(self.address, self.caller)
		print "\tRegisters:"
		print "\t\tEAX: 0x%08x" % (self.registers.eax)
		print "\t\tECX: 0x%08x" % (self.registers.ecx)
		print "\t\tEDX: 0x%08x" % (self.registers.edx)
		print "\t\tEBX: 0x%08x" % (self.registers.ebx)
		print "\t\tESP: 0x%08x" % (self.registers.esp)
		print "\t\tEBP: 0x%08x" % (self.registers.ebp)
		print "\t\tESI: 0x%08x" % (self.registers.esi)
		print "\t\tEDI: 0x%08x" % (self.registers.edi)
		print "\t\tflags: 0x%08x" % (self.registers.flags)
		for i in xrange(1, 8):
			if i == 1:
				t = ""
			else:
				t = "+%X"%((i-1)*4)
			a = self.getArg(i)
			b = self.getStringArg(i)
			if b is None:
				print "\t[ESP%s]: 0x%08x" % (t, a)
			else:
				print "\t[ESP%s]: 0x%08x ('%s')" % (t, a, b)

	def getArg(self, attrNum):
		"""1 based argument getter function"""
		add = (attrNum - 1) * 4 #4 byte paramters
		return gdetour.readDWORD(self.registers.esp+add)

	def getStringArg(self, attrNum):
		addr = self.getArg(attrNum)
		return gdetour.readASCIIZ(addr)

	def getConfiguration(self):
		n = ["bytesToPop", "executeOriginal"]
		return dict(zip(n, gdetour.getDetourSettings(self.address)))

	def setConfiguration(self, settingsDict):
		n = ["bytesToPop", "executeOriginal"]
		p = []
		for x in n:
			p.append(settingsDict[x])
		gdetour.setDetourSettings(self.address, p)

	def changeConfiguration(self, settingname, settingvalue):
		d = self.getConfiguration()
		d[settingname] = settingvalue
		self.setConfiguration(d)



detour_list = {}
class Detour:
	def __init__(self, address, overwrite_len, bytes_to_pop, return_to_original, callback=None, type=0):
		"""
			If return_to_original is true, then bytes_to_pop is not important.
			Conversely, if it is false, overwrite_len is not important.
		"""
		if address in detour_list:
			raise Exception, "Detour already exists!"
		gdetour.createDetour(address, overwrite_len, bytes_to_pop, type)
		gdetour.setDetourSettings(address, (bytes_to_pop, return_to_original))
		self.config = pyDetourConfig(address)
		self.config.callback = callback
		detour_list[address] = self

	def removeDetour(self):
		raise NotImplementedError

	@classmethod
	def do_callback(cls, address, registers, caller):
		if address not in detour_list:
			raise Exception, "Detour... doesn't exist...?"
		if callable(detour_list[address].config.callback):
			detour_list[address].config.callback(callback_obj(address, registers, caller))



def main_callback(*args, **kwargs):
	detouraddr, r, flags, caller = args[0], args[1], args[2], args[3]
	registers = register_list(r, flags)

	Detour.do_callback(detouraddr, registers, caller)


gdetour.callback = main_callback	


##############################################################
##############################################################
##############################################################
##############################################################

def testcb(d):
	d.dump()
	print "\n" + repr(d.getConfiguration())
	

x = Detour(0x00ef1000, 6, 4, True, testcb)