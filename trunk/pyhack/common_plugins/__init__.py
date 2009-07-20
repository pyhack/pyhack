import os
import imp
import logging
import sys

import pyhack.inside_api
from pyhack.util.paths import Paths

log = logging.getLogger(__name__)

class _CommonPlugins(dict):
    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
            
plugins = _CommonPlugins()

def parsePluginModule(module):
    global plugins
    import pdb
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        #if "Patch" in attr_name:
        #    pdb.set_trace()
        try:
            if issubclass(attr, pyhack.inside_api.CommonPlugin):
                plugins[attr_name] =  attr
        except TypeError:
            pass

def loadCommonPlugins():
    log.info("Scanning for common plugins")
    for f in os.listdir(Paths.common_plugins):
        if f.endswith(".py") and not f.startswith("_"):
            modname, junk = os.path.splitext(f)
            try:
                me = __import__(__name__, fromlist=[modname])
                mod = getattr(me, modname)
            except Exception:
                log.exception("Encountered exception loading common plugin module %s"%(f))
                pass
                #import pdb
                #import sys
                #import traceback
                #traceback.print_exc()
                #print
                #pdb.post_mortem(sys.exc_info()[2])
            else:
                log.debug("Found plugin module %s", f)
                parsePluginModule(mod)
loadCommonPlugins()

