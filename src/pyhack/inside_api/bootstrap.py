"""This file is the main starting point for the python interpreter when in the target's process.
It needs to setup the paths, and then import the real target script"""

import sys
print sys.path
print sys.executable



import logging
class DiscardFilter(logging.Filter):
    def filter(self, record):
        if logging.Filter.filter(self, record) == 1:
            return 0
        return 1
        
log = logging.getLogger()
log.setLevel(logging.DEBUG)

log_console_handler = logging.StreamHandler()
log_console_handler.setLevel(logging.DEBUG)
log_console_formatter = logging.Formatter("%(funcName)s: %(message)s")
log_console_handler.setFormatter(log_console_formatter)
#log_console_handler.addFilter(DiscardFilter('pyhack.inside_api'))
log.addHandler(log_console_handler)



log_fh = logging.FileHandler("pyhack_last_run.txt", "w")
log_ff = logging.Formatter("%(asctime)-15s %(levelname)-8s %(name)s.%(funcName)s [%(lineno)s]: %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
log_fh.setFormatter(log_ff)
log.addHandler(log_fh)

log = logging.getLogger(__name__)

import os, pickle, sys, imp

sys.path.append(os.environ['pyHack_ParentPath']) #This lets us import pyhack

conf = pickle.loads(os.environ['pyHack_Config'])
sys.path.append(os.path.dirname(conf['dll'])) #This lets us import _detour


targetDef = conf['targetDef']


import _detour
import pyhack
import pyhack.apps #Prevents 'parent module not loaded' errors
import pyhack.inside_api
__name__ = "pyhack.inside_api.bootstrap"





modname = os.path.splitext(os.path.basename(targetDef.pycode))[0]

log.info("Importing pyhack.apps.%s from inside target"%(modname, ))
with open(targetDef.pycode, "rb") as f:
    try:
        mod = imp.load_source("pyhack.apps." + modname, targetDef.pycode, f)
    except Exception:
        log.exception("Encountered exception in processing plugin")
        import pdb
        import sys
        import traceback
        traceback.print_exc()
        print
        pdb.post_mortem(sys.exc_info()[2])
    else:
        log.info("Sucessfully imported pyhack.apps.%s. Running main()...")
        try:
            continue_mainloop = mod.main(conf)
        except Exception:
            continue_mainloop = False
            log.exception("Encountered exception in plugin's main() function")
            import pdb
            import sys
            import traceback
            traceback.print_exc()
            print
            pdb.post_mortem(sys.exc_info()[2])

import threading


from pyhack.util.debug import interact, resumeThread, debug_on_exception

class InterpreterLoop(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(InterpreterLoop, self).__init__(*args, **kwargs)
        self.daemon = True
    def run(self):
        while True:
            interact(globals(), mod.__dict__, banner="In Mainloop.")

if continue_mainloop is not False:
    mt = InterpreterLoop()
    mt.start()