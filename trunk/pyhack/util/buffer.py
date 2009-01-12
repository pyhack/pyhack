import struct
import ctypes
class Buffer:
	def __init__(self, maxlen):
		self.buf = ctypes.create_string_buffer(maxlen)
		self.i = 0
	def push(self, x):
		if isinstance(x, list):
			for o in x:
				self.push(o)
			return
		if isinstance(x, int):
			x = chr(x)
		i = self.i
		self.buf[i:i+len(x)] = x
		self.i += len(x)
	def _appendBYTE(self, dw, pos=None):
		if dw < 0 or dw >= 2**8: raise ValueError()
		if pos is None:
			struct.pack_into("B", self.buf, self.i, dw)
			self.i += 1
		else:
			struct.pack_into("B", self.buf, pos, dw)
	def _appendWORD(self, dw, pos=None):
		if dw < 0 or dw >= 2**16: raise ValueError()
		if pos is None:
			struct.pack_into("H", self.buf, self.i, dw)
			self.i += 2
		else:
			struct.pack_into("H", self.buf, pos, dw)
	def _appendDWORD(self, dw, pos=None):
		if dw < 0 or dw >= 2**32: raise ValueError()
		if pos is None:
			struct.pack_into("L", self.buf, self.i, dw)
			self.i += 4
		else:
			struct.pack_into("L", self.buf, pos, dw)
class ASMBuffer(Buffer):
	def __init__(self, maxlen):
		Buffer.__init__(self, maxlen)
		self.namedJumps = {}
	def pushAddr(self, addr):
		self.push(0x68)
		self._appendDWORD(addr)
	def movEAX_Addr(self, addr):
		self.push(0xB8)
		self._appendDWORD(addr)
	def callEAX(self):
		self.push([0xFF, 0xD0])
	def pushEAX(self):
		self.push(0x50)
	def INT3(self):
		self.push(0xCC)
	def pushByte(self, b):
		self.push(0x6A)
		self._appendBYTE(b)
	def cmpEAX_Byte(self, b):
		self.push([0x83, 0xF8])
		self._appendBYTE(b)
	def namedJNZ(self, name):
		self.namedJumps[name] = {'jmpLen': 1, 'start': self.i, 'end': None, 'dist': None }
		self.push(0x75)
		self.push(0x00) #this gets filled in
	def nameTarget(self,name):
		if name not in self.namedJumps:
			raise KeyError
		nj = self.namedJumps[name]
		nj['end'] = self.i
		nj['dist'] = nj['end'] - nj['start']
		self._appendBYTE(nj['dist'], nj['start']+nj['jmpLen'])
		self.push(0x90)