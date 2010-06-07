#!/usr/bin/env python
"""
This file is run outside of the process as a launcher.
It's purpose is to decide what application to inject into, and app is associated with it.
"""
import os
import sys
_runMain = False
if __name__ == "__main__":
    #This fun sequence of code lets us redefine this module from being standalone to being part of a package.
    #In turn, that allows up to get all the benifits of being in a package hierarchy,
    #namely, a revised import order (check package dirs first) and better pickling (with full package names).
    #The latter is required to send pickled objects to the child, and to ensure that things work well over there in general.
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    
    import pyhack
    __name__ = "pyhack.launchHack"
    _runMain = True

import logging

logging.basicConfig(
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S',
    format="%(asctime)-15s %(levelname)-8s %(name)s %(funcName)s: %(message)s",
)
log = logging.getLogger()

import sys
import os
import pickle
import pprint

from util.paths import Paths
#sys.path.insert(0, Paths.trunk)

from launcher_api.launcher import TargetLauncher, TargetLaunchException
from launcher_api.targetDef import makeTargets

from util.debug import *



targets = makeTargets({
    'randomNumber': {
        'exe': Paths.testapps + r"\randomNumber\Release\randomNumber.exe",
        'startIn': Paths.testapps + r"\randomNumber\Release",
        'args': r"",
        'pycode': Paths.pycode + r"\randomNumber.py",
    }
})

def main(argv):
    #pdb()
    log.info("Welcome to pyHack.")
    log.info("launchHack.py initializing.")
    
    
    targetName = argv[1]
    try:
        targetDef = targets[targetName]
    except KeyError:
        log.error("A valid targetName was not passed.")
        log.error("Valid targetNames: %s"%(targets.keys()))
        return 1
    
    log.info("Found targetDef for %s."%(targetName))
    log.debug("targetDef: %s"%(pprint.pformat(targetDef)))
    
    path_dll = Paths.get_dll_path(debug=False)#True)
    l = TargetLauncher(
        dll = path_dll,
        pyHome = Paths.pyhome,
        targetDef = targetDef,
    )
    try:
        p = l.launch()
    except TargetLaunchException, e:
        log.exception("")
        log.error(e.message)
        log.error("Failed to launch target. Goodbye.")
        return 2

    log.info("Resuming main thread")
    #p.resume()
    
    #interact(globals(), locals())

    log.info("Goodbye.")
    
if _runMain:
    sys.exit(main(sys.argv))
    if False: #Generally, we don't really want to debug here.
        try:
            sys.exit(main(sys.argv))
        except Exception:
            import pdb
            import sys
            import traceback
            traceback.print_exc()
            print
            pdb.post_mortem(sys.exc_info()[2])
