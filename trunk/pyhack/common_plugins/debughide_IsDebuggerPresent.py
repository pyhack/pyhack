import sys

import pyhack
import pyhack.inside_api
from pyhack.inside_api.detour import Detour
from pyhack.inside_api.common_detours import getProcAddress


class IsDebuggerPresentPatch(pyhack.inside_api.CommonPlugin):
    name = "debughide_IsDebuggerPresent"
    def plugin_init(self):
        self.detours.append(Detour(
            getProcAddress("kernel32.dll::IsDebuggerPresent"),
            False,
            returnFalse
        ))