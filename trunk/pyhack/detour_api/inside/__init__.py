
import pydetour

import detour
from detour import *


memory = pydetour.memory

from common_detours import getPatch as getCommonPatch, CommonPatch

from patch_manager import PatchManager
__all__ = ['misc', 'memory', 'getCommonPatch', 'PatchManager']
__all__.extend(detour.__all__)