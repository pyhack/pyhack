import sys

import pyhack
import pyhack.inside_api
from pyhack.inside_api.detour import Detour
from pyhack.inside_api.common_detours import getProcAddress

import pydetour

class NoOutputDebugString(pyhack.inside_api.CommonPlugin):
    name = "OutputDebugString pass"
    def plugin_init(self):
        o_d_s_addr = getProcAddress("kernel32.dll::OutputDebugStringA")
        #We can't detour it - it'd be recursive.
        #I can't just run the line below yet - I need to add VirtualProtect() calls to pydetour.memory
        pydetour.memory[o_d_s_addr] = "C20400".decode("hex") #RETN 4