import ctypes
import os
import logging
import imp


from .detour import Detour

from ..util.paths import Paths

log = logging.getLogger(__name__)
kernel32 = ctypes.windll.kernel32

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

class CommonPlugin(object):
    def __init__(self):
        self.detours = []
        self.plugin_init()
    def plugin_init(self):
        pass
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