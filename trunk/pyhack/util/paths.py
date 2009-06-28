import os

class Paths:
	"""Contains static methods for properly determining important paths"""
	
	@classmethod
	def setPaths(cls):
		"""Sets this object up with the proper paths"""
		util_path = os.path.dirname(__file__) #'Z:\\pyhack\\trunk\\pyhack\\util'
		pyHack_path = os.path.dirname(util_path) #'Z:\\pyhack\\trunk\\pyhack'
		trunk_path = os.path.dirname(pyHack_path) #'Z:\\pyhack\\trunk'
		svn_top_path = os.path.dirname(trunk_path) #'Z:\\pyhack'

		cls.pyHack = pyHack_path
		cls.trunk = trunk_path
		cls.svn = svn_top_path
	
		cls.pyhome = os.path.join(cls.svn, r"python") #'Z:\\pyhack\\python'
		cls.testapps = os.path.join(cls.svn, r"testApps") #'Z:\\pyhack\\testApps'
		cls.pycode = os.path.join(cls.pyHack, r"apps") #'Z:\\pyhack\\trunk\\pyhack\\apps'

		cls.inside_bootstrap_py = os.path.join(cls.pyHack, r"detour_api\inside\bootstrap.py")

	@classmethod
	def get_dll_path(cls, debug=True):
		"""Assuming this is run from the matching SVN path, returns the path to the dll"""
		if debug:
			return os.path.join(cls.trunk, r"toolkit\Debug\pydetour_d.pyd") #'Z:\\pyhack\\trunk\\toolkit\\Debug\\pydetour_d.pyd'
		else:
			return os.path.join(cls.trunk, r"toolkit\Release\pydetour.pyd") #'Z:\\pyhack\\trunk\\toolkit\\Release\\pydetour.pyd'

Paths.setPaths()
