import logging
log = logging.getLogger(__name__)

import sys
import ctypes

import pyhack
import pyhack.inside_api as api
from pyhack.inside_api.detour import Detour
from pyhack.inside_api import DetourAccessViolationException
from pyhack.inside_api.common_detours import getProcAddress

kernel32 = ctypes.windll.kernel32

class NoTopMostPlugin(pyhack.inside_api.CommonPlugin):
    def __init__(self):
        super(NoTopMostPlugin, self).__init__()
        self.hModule_user32 = kernel32.LoadLibraryA("user32.dll")

        self.detours.append(api.Detour(
            getProcAddress("user32.dll::CreateWindowExA"),
            True,
            lambda d: self.hook_CreateWindowEx('a', d)
        ))

        self.detours.append(api.Detour(
            getProcAddress("user32.dll::CreateWindowExW"),
            True,
            lambda d: self.hook_CreateWindowEx('w', d)
        ))

        self.detours.append(api.Detour(
            getProcAddress("user32.dll::SetWindowPos"),
            True,
            self.hook_SetWindowPos
        ))

    def __del__(self):
        kernel32.FreeLibrary(self.hModule_user32)
        
    def hook_CreateWindowEx(self, which, dtr):
        WS_EX_TOPMOST = 0x00000008
        WS_POPUP = 0x80000000
        WS_CAPTION = 0x00C00000     #WS_BORDER | WS_DLGFRAME
        WS_SYSMENU = 0x00080000
        WS_MINIMIZEBOX = 0x00020000

        #dtr.dump()
        #log.debug("Arguments to CreateWindowEx%s():"%(which.upper()))
        #dtr.dump_stack(1, 12)
        
        lpClass = ""
        dwExStyle = dtr.getStackValue(1)
        if which == 'w':
            try:
                lpClass = dtr.getUnicodeStackValue(2)
            except DetourAccessViolationException:
                pass
            lpWindowName = dtr.getUnicodeStackValue(3)
        else:
            try:
                lpClass = dtr.getStringStackValue(2)
            except DetourAccessViolationException:
                pass
            lpWindowName = dtr.getStringStackValue(3)
        dwStyle = dtr.getStackValue(4)
        log.debug("Old Ex Style: %#x"%(dwExStyle))
        log.debug("Window Class: %s"%(lpWindowName))
        log.debug("Window Name: %s"%(lpWindowName))
        log.debug("Old Style: %#x"%(dwStyle))
        dwExStyle = dwExStyle & ~WS_EX_TOPMOST
        dwStyle = dwStyle | WS_POPUP | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX
        log.debug("New Ex Style: %#x"%(dwExStyle))
        log.debug("New Style: %#x"%(dwStyle))

        dtr.setStackValue(1, dwExStyle)
        dtr.setStackValue(4, dwStyle)
        
        #interact(globals(), locals())
        #dtr.debug_break()
    def hook_SetWindowPos(self, dtr):
        HWND_TOP = 0
        HWND_BOTTOM = 1
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2

        #dtr.dump()
        log.debug("Arguments to SetWindowPos():")
        dtr.dump_stack(1, 7)
        
        log.debug("Old Insert After: %#x"%(dtr.getStackValue(2)))
        if dtr.getStackValue(1) == HWND_TOPMOST:
            dtr.setStackValue(1, HWND_NOTOPMOST)
        log.debug("New Insert After: %#x"%(dtr.getStackValue(1)))
        
        #interact(globals(), locals())
        #dtr.debug_break()