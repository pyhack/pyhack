import logging
log = logging.getLogger(__name__)

import sys
import ctypes
from ctypes import *

import pyhack
import pyhack.inside_api as api
from pyhack.inside_api.detour import Detour
from pyhack.inside_api.common_detours import getProcAddress

from pyhack.util.debug import interact, resumeThread, debug_on_exception

import pydetour

kernel32 = ctypes.windll.kernel32

class D3DHookService(api.CommonPlugin):
    def plugin_init(self):
        self.hModule_d3d = kernel32.LoadLibraryA("d3d9.dll")

        self.d3d_cr_addr = kernel32.GetProcAddress(self.hModule_d3d, "Direct3DCreate9")
        
        self.detours.append(api.Detour(
            self.d3d_cr_addr,
            False,
            self.hook_Direct3DCreate9
        ))
    #@debug_on_exception
    def hook_Direct3DCreate9(self, dtr):
        print "In hook_Direct3DCreate9"
        #eventually we want to do this:
        ret = dtr.callOriginal(dtr.getStackValue(1))
        
        # d3d_cr_ft = WINFUNCTYPE(c_int, c_int)
        # x = dtr.getConfiguration()['originalCodeAddress']
        # d3d_cr = d3d_cr_ft(x)
        # ret = d3d_cr(dtr.getStackValue(1))

        dtr.registers.eax = ret
        self.p_IDirect3D9 = ret

        #log.debug("found original d3d_create at %#x"%(x))
        log.debug("got back p_IDirect3D9 at %#x"%(ret))
        log.debug("IDirect3D9 at %#x"%(dtr.memory[self.p_IDirect3D9].dword))
        #interact(globals(), locals())

        #here we hook some other functions
        self.make_post_IDirect3D9_Create_detours(dtr)
    def make_post_IDirect3D9_Create_detours(self, dtr):
        if getattr(self, "AppliedPostMainInterfaceHooks", False):
            return #We did this already
        log.debug("Creating D3D Post IDirect3D9 call")
        self.AppliedPostMainInterfaceHooks = True
        self.detours.append(api.Detour(
            (dtr.memory[self.p_IDirect3D9] >> (4*2)).dword,
            True,
            self.hook_IDirect3D9_Release
        ).apply())
        self.detours.append(api.Detour(
            (dtr.memory[self.p_IDirect3D9] >> (4*16)).dword,
            False,
            self.hook_IDirect3D9_CreateDevice
        ).apply())
    def hook_IDirect3D9_Release(self, dtr):
        self.p_IDirect3D9 = None


    @debug_on_exception
    def hook_IDirect3D9_CreateDevice(self, dtr):
        #Oh god oh god its COM
        #STDMETHOD(CreateDevice)(THIS_ UINT Adapter,D3DDEVTYPE DeviceType,HWND hFocusWindow,DWORD BehaviorFlags,D3DPRESENT_PARAMETERS* pPresentationParameters,IDirect3DDevice9** ppReturnedDeviceInterface) PURE;
        log.debug("In hook_IDirect3D9_CreateDevice")
        #interact(globals(), locals())
        
        d3d_cd_ft = WINFUNCTYPE(c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int)
        x = dtr.getConfiguration()['originalCodeAddress']
        d3d_cr = d3d_cd_ft(x)
        p_d3dpp = dtr.getStackValue(6)
        dtr.memory[p_d3dpp][4*8].dword = 1 #Windowed
        dtr.memory[p_d3dpp][4*12].dword = 0 #"/* FullScreen_RefreshRateInHz must be zero for Windowed mode */"
        #interact(globals(), locals())
        log.debug("setting break")
        #dtr.set_break(True)
        log.debug("calling original IDirect3D9_CreateDevice")
        ret = d3d_cr(*dtr.getStackValues(1,7))
        log.debug("got %#x", ret)
        dtr.registers.eax = ret
        self.p_d3d_device = dtr.getStackValue(7)
        log.debug("got device at %#x (%#x)", self.p_d3d_device, dtr.memory[self.p_d3d_device].dword)
        
    def __del__(self):
        kernel32.FreeLibrary(self.hModule_d3d)