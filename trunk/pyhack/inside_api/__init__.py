
import pydetour

import detour
from detour import *


memory = pydetour.memory

import common_detours
from common_detours import CommonPlugin

from patch_manager import PatchManager


__all__ = ['misc', 'memory', 'PatchManager']
__all__.extend(detour.__all__)