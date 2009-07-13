from detour import Detour
import ctypes
kernel32 = ctypes.windll.kernel32

import pydetour

class CommonPatchNotFoundException(Exception):
    pass

def returnTrue(d):
    d.registers.eax = 1

def returnFalse(d):
    d.registers.eax = 0

def getProcAddress(what):
    dllName, func = what.split("::")
    hM = kernel32.GetModuleHandleA(dllName)
    if hM == 0:
        return 0
    return kernel32.GetProcAddress(hM, func)

class CommonPatch(object):
    def __init__(self):
        self.detours = []
    def apply(self):
        for i in self.detours:
            i.apply()
        return self
    def remove(self):
        for i in self.detours:
            i.remove()
        return self
    def __repr__(self):
        countApplied = sum([1 for x in self.detours if x.applied is True])
        return "<%s %s (%s/%s)>"%(
            self.__class__.__name__.split(".")[-1],
            ["Disabled", "Enabled"][countApplied == len(self.detours)],
            countApplied,
            len(self.detours)
        )
            

class IsDebuggerPresentPatch(CommonPatch):
    def __init__(self):
        CommonPatch.__init__(self)
        d = Detour(getProcAddress("kernel32.dll::IsDebuggerPresent"), False, returnFalse)
        d.name = "IsDebuggerPresent? No."
        self.detours.append(d)

class NoOutputDebugString(CommonPatch):
    def __init__(self):
        super(NoOutputDebugString, self).__init__()

        o_d_s_addr = getProcAddress("kernel32.dll::OutputDebugStringA")
        #We can't detour it - it'd be recursive.
        #I can't just run the line below yet - I need to add VirtualProtect() calls to pydetour.memory
        pydetour.memory[o_d_s_addr] = "C20400".decode("hex") #RETN 4

c = {
    'kernel32.IsDebuggerPresent': IsDebuggerPresentPatch(),
    #'kernel32.OutputDebugString': NoOutputDebugString(),
}

__all__ = ['getPatch', 'CommonPatch']
def getPatch(patchName):
    if patchName in c:
        return c[patchName]
    raise CommonPatchNotFoundException(patchName)
