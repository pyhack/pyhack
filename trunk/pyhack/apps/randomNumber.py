#Below line is not needed, just an example of relative imports
from ..util.paths import Paths

#from pyhack.util.app import APPlugin
import pyhack.inside_api as api
from pyhack.util.debug import interact

class NumberPatch(api.CommonPatch):
	"""NumberPatch detours the target's getRandomNumber() function to return 42"""
	
	offs = {
		'isValid' : 0xC11030,
		'getRandomNumber' : 0xC11000,
	}

	def __init__(self):
		api.CommonPatch.__init__(self)
		dtr = api.Detour(
			NumberPatch.offs['getRandomNumber'], 
			False,
			self.return42
		)
		name = "Random -> 42"
		self.detours.append(dtr)
		
	def return42(self, dtr):
		dtr.registers.eax = 42

patches = (
	("number", NumberPatch(), True),
)

m = api.memory

p = api.PatchManager()
p.addCommonPatch("kernel32.IsDebuggerPresent").apply()
p['number'] = NumberPatch()
p['number'].apply()

import pprint
pprint.pprint(p)

interact(globals(), locals())