from pyhack.util.app import APPlugin
from pyhack import detour_api

class NumberPatch(detour_api.CommonPatch):
	"""NumberPatch detours the target's getRandomNumber() function to return 42"""
	
	offs = {
		'isValid' : 0x00401030,
		'getRandomNumber' : 0x00401000,
	}

	def __init__(self):
		detour_api.CommonPatch.__init__(self)
		dtr = detour_api.Detour(
			NumberPatch.offs['getRandomNumber'], 
			False, self.return42
		)
		name = "IsDebuggerPresent? No."
		self.detours.append(dtr)
		
	def return42(self, dtr):
		dtr.registers.eax = 42

patches = (
     # name,	patch,	apply
	("number", NumberPatch(), True),
)

APPlugin(patches).go()
