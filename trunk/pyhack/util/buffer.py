"""
:mod:`util.buffer` module
-----------------------------

.. autoclass:: Buffer
    :members:
    :undoc-members:
    
.. autoclass:: ASMBuffer
    :members:
    :undoc-members:
    
"""
import struct
import ctypes
class Buffer:
    """Simple dumb buffer that allows for easy manipulation. Call push([0xbyte, 0xbyte]).
    
    Designed as a simple buffer abstraction, `Buffer` keeps track of a `cursor` pointing
    to the current insertation point. Calling `Buffer.push` will move this cursor forward
    after the append operation.
    
    Convience methods are `Buffer.appendBYTE`, `Buffer.appendWORD`, and `Buffer.appendDWORD`
    which, given an integer, calls push() with the in-memory representation of the integer. This
    representation is 1, 2, or 4 bytes, respectively.
    """
    def __init__(self, maxlen):
        self.buf = ctypes.create_string_buffer(maxlen)
        self.cursor = 0
    def push(self, x):
        if isinstance(x, (list, tuple)):
            for o in x:
                self.push(o)
            return
        if isinstance(x, int):
            x = chr(x)
        i = self.cursor
        self.buf[i:i+len(x)] = x
        self.cursor += len(x)
    def _appendBYTE(self, dw, pos=None):
        if dw < 0 or dw >= 2**8: raise ValueError()
        if pos is None:
            struct.pack_into("B", self.buf, self.cursor, dw)
            self.cursor += 1
        else:
            struct.pack_into("B", self.buf, pos, dw)
    def _appendWORD(self, dw, pos=None):
        if dw < 0 or dw >= 2**16: raise ValueError()
        if pos is None:
            struct.pack_into("H", self.buf, self.cursor, dw)
            self.cursor += 2
        else:
            struct.pack_into("H", self.buf, pos, dw)
    def _appendDWORD(self, dw, pos=None):
        if dw < 0 or dw >= 2**32: raise ValueError()
        if pos is None:
            struct.pack_into("L", self.buf, self.cursor, dw)
            self.cursor += 4
        else:
            struct.pack_into("L", self.buf, pos, dw)


_ASM_BUFFER_JUMP_FILLED_IN = object()
class ASMBuffer_TargetFilledException(Exception):
    """Indicates that a `ASMBuffer.nameTarget` has already been called for the specified named jump."""

    
class ASMBuffer_TargetNotFilledException(Exception):
    """Indicates that a `ASMBuffer.nameTarget` has not been called for the specified named jump."""

    
class ASMBuffer(Buffer):
    """Buffer meant to hold x86 assembler opcodes.
    
    `ASMBuffer` is designed so that calling it's methods will add an opcode of the desired type
    to the buffer by calling `Buffer.push`.
    
    Most methods are self explanitory, except for the 'named JMP' series of functions (for example,
    `ASMBuffer.namedJZ`). Using these methods, in combination with `ASMBuffer.nameTarget`, allows one
    to simply name portions of the ASM code that is being fed into this buffer. 
    
    .. warning:: `ASMBuffer.nameTarget` must be called *after* the cooresponding 'named JMP' function(s). That is,
       assembler code can only 'jump forward'. This is a design limitation.
    
    .. note:: `ASMBuffer.nameTarget` will first emit two bytes of 0xCC, that is, INT 3 unless allowFlowThrough=True
       is passed as a keyword argument.
    """
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
    def pushDword(self, b):
        self.push(0x68)
        self._appendDWORD(b)
    def pushByte(self, b):
        self.push(0x6A)
        self._appendBYTE(b)
    def cmpEAX_Byte(self, b):
        self.push([0x83, 0xF8])
        self._appendBYTE(b)
    def addESP(self, b):
        self.push([0x83, 0xC4])
        self._appendBYTE(b)
    def addEAX(self, b):
        self.push([0x83, 0xC0])
        self._appendBYTE(b)
    def namedJZ(self, name):
        if name not in self.namedJumps:
            self.namedJumps[name] = []
        if self.namedJumps[name] == _ASM_BUFFER_JUMP_FILLED_IN:
            raise ASMBuffer_TargetFilledException(name)
        thisJump = {}
        thisJump['start'] = self.cursor
        self.push(0x74)
        thisJump['start_d'] = self.cursor
        self.push(0x00) #this gets filled in
        thisJump['beginjmp'] = self.cursor
        self.namedJumps[name].append(thisJump)
    def namedJNZ(self, name):
        if name not in self.namedJumps:
            self.namedJumps[name] = []
        if self.namedJumps[name] == _ASM_BUFFER_JUMP_FILLED_IN:
            raise ASMBuffer_TargetFilledException(name)
        thisJump = {}
        thisJump['start'] = self.cursor
        self.push(0x75)
        thisJump['start_d'] = self.cursor
        self.push(0x00) #this gets filled in
        thisJump['beginjmp'] = self.cursor
        self.namedJumps[name].append(thisJump)
    def nameTarget(self, name, allowFlowThrough=False):
        if not allowFlowThrough:
            self._appendBYTE(0xCC)
            self._appendBYTE(0xCC)
        if name not in self.namedJumps:
            raise KeyError
        nj_list = self.namedJumps[name]
        for nj in nj_list:
            nj['end'] = self.cursor
            nj['dist'] = nj['end'] - nj['beginjmp']
            self._appendBYTE(nj['dist'], nj['start_d'])
            nj = _ASM_BUFFER_JUMP_FILLED_IN
    def verifyJumps(self, ignoreSuccess_labels=True):
        bads = set()
        for name, v in self.namedJumps.iteritems():
            if ignoreSuccess_labels and "success" in name:
                continue
            for nj in v:
                if nj != _ASM_BUFFER_JUMP_FILLED_IN:
                    bads.add(name)
        if bads:
            raise ASMBuffer_TargetNotFilledException(bads)
