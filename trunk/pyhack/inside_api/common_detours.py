from detour import Detour
import ctypes
kernel32 = ctypes.windll.kernel32

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
    def remove(self):
        for i in self.detours:
            i.remove()
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



c = {
    'kernel32.IsDebuggerPresent': IsDebuggerPresentPatch(),
}

__all__ = ['getPatch', 'CommonPatch']
def getPatch(patchName):
    if patchName in c:
        return c[patchName]
    raise CommonPatchNotFoundException(patchName)
