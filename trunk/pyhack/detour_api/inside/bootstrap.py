"""This file is the main starting point for the python interpreter when in the target's process.
It needs to setup the paths, and then import the real target script"""

import os, pickle, sys, imp

sys.path.append(os.environ['pyHack_ParentPath']) #This lets us import pyhack

conf = pickle.loads(os.environ['pyHack_Config'])
sys.path.append(os.path.dirname(conf['dll'])) #This lets us import pydetour


targetDef = conf['targetDef']


import pydetour
import pyhack
import pyhack.apps #Prevents 'parent module not loaded' errors

modname = os.path.splitext(os.path.basename(targetDef.pycode))

with open(targetDef.pycode, "rb") as f:
	mod = imp.load_source("pyhack.apps." + modname[0], targetDef.pycode, f)