import os
import sys
import pickle
import logging
import pprint
import ctypes
kernel32 = ctypes.windll.kernel32


from pyhack import detour_api

class APPlugin(object):
	def __init__(self, patches):
		self._setup_target_environ(ENVCONFVAR)
		self._setup_logging()
		
		self.memory = detour_api.memory
		self.patches = detour_api.PatchManager()
		# Hide from debugger
		self.patches.addCommonPatch("kernel32.IsDebuggerPresent").apply()
		
		pyVersion = "%s.%s.%s %s" % tuple(sys.version_info[:4])
		if detour_api.misc.pythonDebug:
			self.log.info("Running under Python DEBUG version %s" % pyVersion)
		else:
			self.log.info("Running under Python RELEASE version %s" % pyVersion)
		
		for name, patch, apply in patches:
			self.patches[name] = patch
			if apply:
				self.patches[name].apply()
				pprint.pprint(self.patches[name])
				
	def go(self):
		detour_api.misc.interact(globals(), locals())
		
	
	def _setup_logging(self):
		self.rootlog = logging.getLogger("")
		self.rootlog.setLevel(logging.DEBUG)
		handler = logging.StreamHandler()
		handler.setLevel(logging.DEBUG)
		format = logging.Formatter(
		    "%(asctime)s - %(name)s - %(levelname)s: %(message)s")
		handler.setFormatter(format)
		del format
		del handler
		self.log = logging.getLogger(self.config['targetName'])
		
	def resumeThread(self, thread_id):
		THREAD_SUSPEND_RESUME = 0x0002
		handle = kernel32.OpenThread(THREAD_SUSPEND_RESUME, False, thread_id)
		kernel32.ResumeThread(handle)
		kernel32.CloseHandle(handle)
		
	def returnTrue(self, detour):
		detour.registers.eax = 1
		
	def returnFalse(self, detour):
		detour.registers.eax = 0
			
		