#Below line is not needed, just an example of relative imports
from ..util.paths import Paths

#from pyhack.util.app import APPlugin
import pyhack.inside_api as api
from pyhack.util.debug import interact

class NumberPlugin(api.CommonPlugin):
    """NumberPlugin detours the target's getRandomNumber() function to return 42"""
    
    offs = {
        'isValid' : 0x401030,
        'getRandomNumber' : 0x401000,
    }

    def plugin_init(self):
        dtr = api.Detour(
            NumberPlugin.offs['getRandomNumber'], 
            False,
            self.return42
        )
        name = "Random -> 42"
        self.detours.append(dtr)
        
    def return42(self, dtr):
        dtr.registers.eax = 42

class RandomApplication:
    def __call__(self, conf):
        p = api.PluginManager()
        p['number'] = NumberPlugin().apply()


        import pprint
        pprint.pprint(p)
        interact(globals(), locals())

        return False #Don't continue mainloop / don't give me the interpreter

main = RandomApplication()
