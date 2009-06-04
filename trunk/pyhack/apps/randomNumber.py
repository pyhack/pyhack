#----------------------------------------------------------------
import os, pickle, sys
conf = pickle.loads(os.environ['pyDetourConfig'])
sys.path.append(os.path.dirname(conf['dll']))
sys.path.append(os.path.dirname(conf['targetDef']['pycode']))
#----------------------------------------------------------------
import logging
rootLog = logging.getLogger("")
rootLog.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
ch.setFormatter(formatter) #add formatter to handler
rootLog.addHandler(ch) #add the handlers to logger
del formatter
del ch
log = logging.getLogger(conf['targetName'])
#----------------------------------------------------------------
import pprint
log.info("Configuration:\n" + pprint.pformat(conf))
#----------------------------------------------------------------
import ctypes
kernel32 = ctypes.windll.kernel32

def resumeThread(threadId):
	THREAD_SUSPEND_RESUME = 0x0002
	hThread = kernel32.OpenThread(THREAD_SUSPEND_RESUME, False, threadId)
	kernel32.ResumeThread(hThread)
	kernel32.CloseHandle(hThread)

import detour_api
pyVer = "%s.%s.%s %s"%(sys.version_info[0], sys.version_info[1], sys.version_info[2], sys.version_info[3])
if detour_api.misc.pythonDebug:
	log.info("Running under Python debug version %s"%(pyVer))
else:
	log.info("Running under Python release version%s"%(pyVer))


##############################################################

def returnTrue(d):
	d.registers.eax = 1

def returnFalse(d):
	d.registers.eax = 0

flag = False
def returnTrueOnce(d):
	if not globals()['flag']:
		d.registers.eax = 1
		globals()['flag'] = True
	else:
		d.registers.eax = 0

sym = {}
sym['isValid'] = 0x9A1030
sym['getRandomNumber'] = 0x9A1000

m = detour_api.memory

p = detour_api.PatchManager()
p.addCommonPatch("kernel32.IsDebuggerPresent").apply()

class NumberPatch(detour_api.CommonPatch):
	"""NumberPatch detours the target's getRandomNumber() function to return 42"""
	def __init__(self):
		detour_api.CommonPatch.__init__(self)
		d = detour_api.Detour(sym['getRandomNumber'], False, self.return42)
		name = "IsDebuggerPresent? No."
		self.detours.append(d)
		
	def return42(self, d):
		print self
		print d
		d.registers.eax = 42

p["number"] = NumberPatch()
p["number"].apply()

pprint.pprint(p)
detour_api.misc.interact(globals(), locals())