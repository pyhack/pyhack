Developing `pyhack`
===================

There are two major types of development that one can do when working on the pyhack codebase.
The first is developing the python side, which includes friendly 'user facing' features such as the
simplified detour interface, process launching code, etc.
The second is developing the C extension modules of pyhack, namely `pydetour` and associated modules.

Python extension development on Windows is ... interesting. There are several ways to go about it,
but a quick synoposis is that you need python's header files, your code, and some compilers to put it together.

To complicate things further, extention modules in Python can be built in a debug version and release version.
To complicate things further than /that/, each type of extension module can only be loaded into that type of interpreter.
Whats more, since we're embedding our own interpreter into a target process, our own interpreter can be compiled as either a debug or release build.

It goes without saying that the debug versions of the module are very very handy to have for developing the C extension modules. Of course, since python.org doesn't
distribute a debug version of python binary for windows (as far as I can tell) and we need the include files anyway (to build our modules), it's simplest to create
our own python install too.

To simplify this process, pyhack includes a number of scripts to help you (the developer) out.

Creating a Development Environment
----------------------------------

Prerequisites
^^^^^^^^^^^^^

* Install `Visual Studo 2008 <http://www.microsoft.com/express/Downloads/#2008-All>`_ (`Direct Link <http://download.microsoft.com/download/E/8/E/E8EEB394-7F42-4963-A2D8-29559B738298/VS2008ExpressWithSP1ENUX1504728.iso>`__)
    * Other versions *may* work, but the scripts (both pyhack's and python's) are set up to only use VS 2008.
    * Note that most scripts assume you installed this into it's default path of ``C:\Program Files\Microsoft Visual Studio 9.0`` (``C:\Program Files (x86)\Microsoft Visual Studio 9.0`` on 64 bit machines)
* Install `msysgit <http://code.google.com/p/msysgit/>`_ or another git client
    * Check the value of git's `core.autocrlf <http://stackoverflow.com/questions/2825428/why-should-i-use-core-autocrlf-true-in-git>`_ setting. It should probably be 'true'.
        * Check value: ``git config --global core.autocrlf``
        * Set value: ``git config --global core.autocrlf true``
* Install `cygwin <http://www.cygwin.com/>`_ (`Direct Link <http://cygwin.com/setup.exe>`__)
* Add cygwin's bin directory to the path with one of these methods
    * Globally:
        Follow `these instructions <http://stackoverflow.com/questions/3701646/how-to-add-to-the-pythonpath-in-windows-7/4855685#4855685>`_, but edit the existing PATH variable and append ``C:\cygwin\bin`` (or your custom install location for cygwin)
    * Each time you open a cmd window:
        ``set PATH=%PATH%;C:\cygwin\bin``
        

Setting Up
^^^^^^^^^^^^^

1. ``git clone git://pyhack``
2. ``cd pyhack``
3. ``initial_env_setup.cmd``
    * Downloads and builds Python 2.7.2
    * Installs `pip <http://www.pip-installer.org>`_, `distribute <http://packages.python.org/distribute/>`_, `virtualenv <http://pypi.python.org/pypi/virtualenv>`_, and `sphinx <http://sphinx.pocoo.org/>`_.
    * Generates pyhack documentation in ``trunk/doc/_build/html``
    * Does **not** create a virtualenv, as this is apparenly broken for python running from a source directory.
4. ``rebuild_pyhack.cmd``
    * Uses the python built in step 3 to run ``setup.py develop`` and ``setup.py build -g develop``, which rebuilds pyhack's extension modules and adds pyhack to python's path.

Developing
----------
* You now have both a release and debug build in ``python\PCBuild`` (as ``python.exe`` and ``python_d.exe``)
* ``rebuild_pyhack.cmd`` uses these builds to run ``pyhack\trunk\setup.py develop`` and build both the release and debug extension modules.
* If you edit python source files, changes will take effect with a simple restart (thanks to distribute's `development mode <http://packages.python.org/distribute/setuptools.html#development-mode>`_)
* If you edit C source files, you need to rebuild by running ``rebuild_pyhack.cmd`` again.

Environment
^^^^^^^^^^^^^
* I was unable to get virtualenv to work properly from this source build. I traced it to `issue 139 <https://github.com/pypa/virtualenv/issues/139>` in virtualenv.
* As a result, I use the site-packages folder in ``python\lib``
* You can easily install packages here via ``python\scripts\pip install (package)``
* You may want to add this new python to your path while working in a command window: ``set PATH=%CD%\python\PCbuild;%CD%\python\scripts;%PATH%``

.. toctree::
   :maxdepth: 2