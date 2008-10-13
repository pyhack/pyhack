import imp
x = imp.get_suffixes()[0][0]
if x == "_d.pyd":
        print "Running testcode.py under debugging python version\n"
else:
        print "Running testcode.py under release python version\n"        

print "\n\n"


import pydetour
import ctypes
import pydasm
import struct

#print "testcode.py loaded"

##############################################################
##############################################################
##############################################################
#	Everything in this section should be regarded as API
##############################################################
##############################################################
##############################################################
detour_list = {}

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


##############################################################
####Helper functions
def findOptimalTrampolineLength(address, minlen=5, maxlen=12, noisy=False):
	if noisy: print "Determining optimal tramploine size for address 0x%08x:"%(address)
	buffer = pydetour.util.read(address, maxlen+5)

	l = 0
	ic = 0
	offset = 0
	while l < maxlen:
		i = pydasm.get_instruction(buffer[offset:], pydasm.MODE_32)
		if not i:
			break
		if noisy: print "%d bytes: %s"%(i.length, pydasm.get_instruction_string(i, pydasm.FORMAT_INTEL, 0))
		ic += 1
		offset += i.length
		l += i.length
		if l >= minlen:
			break
	if noisy: print "optimal size is %d bytes (%d instructions)"%(l, ic)
	return l

def findBytesToPop(address, maxlen=512, noisy=False):
	t = None
	if noisy: print "Determining bytes to pop for function at address 0x%08x:"%(address)
	buffer = pydetour.util.read(address, maxlen+5)
	#buffer = "\xC3" #ret
	#buffer = "\xC2\x04" #retn 4
	l = 0
	ic = 0
	offset = 0
	num = None
	while l < maxlen:
		i = pydasm.get_instruction(buffer[offset:], pydasm.MODE_32)
		if not i:
			break
		istr = pydasm.get_instruction_string(i, pydasm.FORMAT_INTEL, 0)
		if noisy: print "%d bytes: %s"%(i.length, istr)
		ic += 1
		offset += i.length
		l += i.length
		if istr.strip() == "ret":
			if noisy: print "found ret instruction (no bytes to pop)"
			num = 0
			t = "cdecl"
			break
		if istr.startswith("retn"):
			if noisy: print i
			num = istr[5:]
			num = int(num, 16)
			t = "stdcall"
			if noisy: print "found retn instruction, bytes to pop = %s"%(num)
			break
	if num is None:
		if noisy: print "warning, no retn instruction found"
	else:
		if noisy: print "bytes to pop is %d bytes (found after %d instructions)"%(num, ic)
	return (t, num)

def ValidReadPtr(addr, len=1):
	return not ctypes.windll.kernel32.IsBadReadPtr(addr, len)
def ValidWritePtr(addr, len=1):
	return not ctypes.windll.kernel32.IsBadWritePtr(addr, len)
def ValidPtr(addr, len=1):
	return ValidWritePtr(addr, len)
def RequireValidPtr(addr, len=1):
	if not ValidPtr(addr, len):
		raise Exception("Invalid Pointer 0x%08x"%(addr))


##############################################################

class pyDetourConfig:
	"""Configuration of a pydetour that can be changed throughout the detour's lifetime"""
	def __init__(self, addr):
		self.address = addr
		self.callback = None
		self.callback_obj = None
		self.functionType = "cdecl"
		self.bytesToPop = 0 #needed for calling originaldef ValidReadPtr(addr, len=1):


##############################################################
class callback_obj:
	"""This is the object passed to function that are registed as callbacks. It should be the only way to interact with pydetour"""

	def __init__(self, address, registers, caller):
		self.address = address	
		self.registers = registers
		self.caller = caller
		self.detour = detour_list[address]

	def applyRegisters(self):
		"""This function is automaticly called after the callback function.
		It will set the registers to what was specified in the object.

		It is possible you will .remove() the detour before this is done.
		In that case, call this function manually before doing so."""
		r = (
			self.registers.eax,
			self.registers.ecx,
			self.registers.edx,
			self.registers.ebx,
			self.registers.esp,
			self.registers.ebp,
			self.registers.esi,
			self.registers.edi,
			)
		return pydetour.setRegisters(self.address, r, self.registers.flags, self.caller)

	@staticmethod
	def read(address, length):
		"""Reads length bytes from address"""
		return pydetour.util.read(address, length)

	@staticmethod
	def write(address, length, bytes):
		"""Writes length bytes to address"""
		return pydetour.util.write(address, length, bytes)

	def dump(self):
		"""Convient utility function to dump information about this function call"""
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
				t = "   "
			else:
				t = "+%02X"%((i-1)*4)
			try:
				a = self.getArg(i)
			except pydetour.DetourAccessViolationException:
				print "\t[ESP%s]: Access Violation"% (t)

			try:
				b = self.getStringArg(i)
				print "\t[ESP%s]: 0x%08x ('%s')" % (t, a, b)				
			except pydetour.DetourAccessViolationException:
				print "\t[ESP%s]: 0x%08x" % (t, a)



	def getArg(self, attrNum):
		"""1 based argument getter function"""
		add = (attrNum - 1) * 4 #4 byte paramters
		return pydetour.util.readDWORD(self.registers.esp+add)

	def setArg(self, attrNum, dword):
		"""1 based argument setter function"""
		add = (attrNum - 1) * 4 #4 byte paramters
		return pydetour.util.writeDWORD(self.registers.esp+add, dword)
	
	def getStringArg(self, attrNum):
		"""1 based argument getted function. Looks up an ASCII string pointed to by the argument."""
		addr = self.getArg(attrNum)
		return pydetour.util.readASCIIZ(addr)

	def getConfiguration(self):
		n = ["bytesToPop", "executeOriginal"]
		return dict(zip(n, pydetour.getDetourSettings(self.address)))

	def setConfiguration(self, settingsDict):
		n = ["bytesToPop", "executeOriginal"]
		p = []
		for x in n:
			p.append(settingsDict[x])
		pydetour.setDetourSettings(self.address, p)

	def changeConfiguration(self, settingname, settingvalue):
		"""Helper funtion to change configuration settings on the fly."""
		d = self.getConfiguration()
		d[settingname] = settingvalue
		self.setConfiguration(d)

	def callOriginal(self, params, registers=None, functiontype=None):
		if (functiontype == None):
			functiontype = self.detour.config.functionType
		if functiontype == "cdecl":
			pass
			#push all the vars
			#call original
			#pop all the vars
		elif functiontype == "stdcall":
			pass
			#push stack magic number
			#push all the vars
			#call original
			#check stack magic number
			#pop all the vars
		else:
			raise Exception("Unsupported function type %s"%(functiontype))
		raise NotImplementedError("Calling original functions not yet supported");
##############################################################
##############################################################

class Detour:
	def __init__(self, address, return_to_original, callback=None, bytes_to_pop=None, overwrite_len=None, type=0, callback_class=None):
		"""
			If return_to_original is true, then bytes_to_pop is not important.
			Conversely, if it is false, overwrite_len is not important.
		"""
		if address in detour_list:
			raise Exception, "Detour already exists!"

		if callable(return_to_original) and callback == None:
			#this if supports constructs like this:
			#x = Detour(0x123, returnTrue)
			callback = return_to_original
			return_to_original = False

		try:

			if overwrite_len is None:
				overwrite_len = findOptimalTrampolineLength(address)
				if overwrite_len < 5 or overwrite_len > 12:
					print "Warning: guessed overwrite_len is %d for function at address 0x%08x"%(overwrite_len, address)

			if bytes_to_pop is None:
				(t, bytes_to_pop) = findBytesToPop(address)
				if bytes_to_pop is None:
					raise Exception("Could not determine number of bytes to pop on return from function at 0x%08x"%(address))
			else:
				t = "stdcall"
			print "Detouring function at 0x%08x (%s%s)"%(address, t, (""," 0x%x bytes"%(bytes_to_pop))[t=="stdcall"])
			
			pydetour.createDetour(address, overwrite_len, bytes_to_pop, type)
			pydetour.setDetourSettings(address, (bytes_to_pop, return_to_original))
			self.config = pyDetourConfig(address)
			self.address = address
			self.config.callback = callback
			self.config.functionType = t
			self.config.bytesToPop = bytes_to_pop
			if callback_class is None:
				callback_class = callback_obj
			self.config.callback_obj = callback_class
			detour_list[address] = self
			
		except pydetour.DetourAccessViolationException:
			raise pydetour.DetourAccessViolationException("Invalid detour address 0x%08x"%(address))

	def remove(self):
		pydetour.removeDetour(self.address)
		self.config = None
		del detour_list[self.address]

	@classmethod
	def do_callback(cls, address, registers, caller):
		if address not in detour_list:
			raise Exception, "Detour... doesn't exist...?"
		if callable(detour_list[address].config.callback):
			try:
				obj = detour_list[address].config.callback_obj(address, registers, caller)
				if obj is None:
					obj = callback_obj(address, registers, caller)
				detour_list[address].config.callback(obj)
			except Exception, e:
				import traceback
				print "Exception in callback for function at address 0x%08x:\n"%(address)
				traceback.print_exc()
				print ""
				#raise e
			try:
				obj.applyRegisters()
			except LookupError: #could have removed the detour from inside the callback function
				pass




def main_callback(*args, **kwargs):
	detouraddr, r, flags, caller = args[0], args[1], args[2], args[3]
	registers = register_list(r, flags)

	Detour.do_callback(detouraddr, registers, caller)


#pydetour.callback = main_callback	


##############################################################
##############################################################
##############################################################
##############################################################

def interact():
	import code
	code.interact(banner="\nIn Python Interactive Loop. Enter Ctrl-Z to continue.", local=globals())

def returnTrue(d):
	d.registers.eax = 1

def returnFalse(d):
	d.registers.eax = 0

flag = False
def returnTrueOnce(d):
	if not globals()['flag']:
		d.registers.eax = 1
		globals()['flag'] = True
	else:
		d.registers.eax = 0
	
def testcb(d):
	d.dump()
	d.registers.eax = 0;
	#d.applyRegisters()
	#d.detour.remove()
	d.callOriginal(("lol whut"))

	
def dword(x):
	if isinstance(x, basestring): #Converting /from/ memory to python int
		if len(x) % 4 != 0:
			raise TypeError("dword() must be called with a byte strings whose size is a multiple of 4. (Got %i bytes)"%(len(x)))
		n = len(x) / 4
		r = struct.unpack("L"*n, x)
		if len(r) == 1:
			return r[0]
		return r
	#Converting /to/ memory layout
	packed = ""
	try:
		for item in x:
			try:
				if item < 0 :
					packed += struct.pack("l", item)
				else:
					packed += struct.pack("L", item)
			except:
				raise TypeError("Could not pack %r into dword"%(item))
	except TypeError:
		item = x
		try:
			if item < 0 :
				packed += struct.pack("l", item)
			else:
				packed += struct.pack("L", item)
		except:
			raise TypeError("Could not pack %r into dword"%(x))
	return packed
def qword(x):
	if isinstance(x, basestring): #Converting /from/ memory to python int
		if len(x) % 8 != 0:
			raise TypeError("qword() must be called with a byte strings whose size is a multiple of 8. (Got %i bytes)"%(len(x)))
		n = len(x) / 8
		r = struct.unpack("Q"*n, x)
		if len(r) == 1:
			return r[0]
		return r
	#Converting /to/ memory layout
	packed = ""
	try:
		for item in x:
			try:
				if item < 0 :
					packed += struct.pack("q", item)
				else:
					packed += struct.pack("Q", item)
			except:
				raise TypeError("Could not pack %r into qword"%(item))
	except TypeError:
		item = x
		try:
			if item < 0 :
				packed += struct.pack("q", item)
			else:
				packed += struct.pack("Q", item)
		except:
			raise TypeError("Could not pack %r into qword"%(x))
	return packed



m = pydetour.memory
interact()

x = Detour(0x00a41140, False, returnTrueOnce)

interact()
