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
import imp

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
        
        At the time of execution, this file may exist in any of the following places:
            * In ``pydetour\Release\_detour.pyd`` if VS 2008 built the file
            * In a temp lib directory if using setup.py build
            * Installed in the pythonpath
            * Installed in trunk dir if installed with setup.py develop
            
        
        Because we're on 2.7, we can't use importlib.
        The source of importlib (in 3.1) checks `the following <http://hg.python.org/cpython/file/6f0bcfc17a9e/Lib/importlib/_bootstrap.py#l885>`_ to load a module::
        
            for finder in sys.meta_path + [BuiltinImporter, FrozenImporter, _DefaultPathFinder]:
                loader = finder.find_module(name, path)
                if loader is not None:
                    loader.load_module(name)
                    break
        
        We can, however, use `imp.find_module <http://docs.python.org/library/imp.html#imp.find_module>`_, which is nearly the same thing::
        
            >>> imp.find_module('_detour')
            (<open file 'z:\pyhack\trunk\_detour.pyd', mode 'rb' at 0x01D85F40>, 'z:\\pyhack\\trunk\\_detour.pyd', ('.pyd', 'rb', 3))
        """
        fm = imp.find_module('_detour')
        if fm[0]:
            fm[0].close()
        module_path = fm[1]
        #module_path may or may not contain _d depending on if /this script/ was run in a debug python
        #We don't care though, so we remove it always...
        module_path = module_path.replace('_detour_d.pyd', '_detour.pyd')
        if debug: #Unless debug was requested
            module_path = module_path.replace('_detour.pyd', '_detour_d.pyd')
        if not os.path.exists(module_path):
            raise ImportError('%s does not exists, have you built the extension modules?'%(module_path))
        return module_path

Paths.setPaths()
