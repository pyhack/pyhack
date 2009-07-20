"""
:mod:`util.paths` module
----------------------------

The :class:`Paths` class is responsible for calculating the absolute paths to 
various required locations used by PyHack.

.. autoclass:: Paths
    :members:
    
The available class-attributes are:
 * **svn_top_path** : Path to the SVN root
 * **trunk_path** : Path to SVN trunk directory
 * **pyhome** : Path to included Python distribution
 * **testapps** : Path to included example targets
 * **pycode** : Path to plugin directory
 * **pyHack** : Path to the PyHack module
 * **common_plugins** : Path to common plugins
"""

import os

class Paths:
    """
    Contains static methods for properly determining important paths
    """
    
    @classmethod
    def setPaths(cls):
        """
        Sets this object up with the proper paths. This method is called on 
        import
        """
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
        cls.inside_bootstrap_py = os.path.join(cls.pyHack, r"inside_api\bootstrap.py")

        cls.common_plugins = os.path.join(cls.pyHack, r"common_plugins")
    @classmethod
    def get_dll_path(cls, debug=True):
        """
        Assuming this is run from the matching SVN path, returns the path to the dll
        """
        if debug:
            return os.path.join(cls.trunk, r"pydetour\Debug\pydetour_d.pyd") #'Z:\\pyhack\\trunk\\pydetour\\Debug\\pydetour_d.pyd'
        else:
            return os.path.join(cls.trunk, r"pydetour\Release\pydetour.pyd") #'Z:\\pyhack\\trunk\\pydetour\\Release\\pydetour.pyd'

Paths.setPaths()
