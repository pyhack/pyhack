r"""
:mod:`util.debug` module
----------------------------

The :mod:`pyhack.util.debug` module is useful for accessing an interactive debugging 
console from within the target. This allows one to explore the process and
make dynamic changes interactively.

.. autodata:: pyhack.util.debug.pythonDebug

.. autofunction:: interact(globals=None, locals=None, banner="\nIn Python Interactive Loop. Enter Ctrl-Z to continue.")

.. autoclass:: SuperInteractiveConsole(code.InteractiveConsole)

.. autofunction:: pdb()

.. autofunction:: resumeThread()
    
"""


import code
import pdb
import imp
import sys

__all__ = [
    'pythonDebug',
    'interact',
    'pdb',
]

pythonDebug = False
"""True when the debug Python environment is present."""

x = imp.get_suffixes()[0][0]
if x == "_d.pyd":
    pythonDebug = True


class SuperInteractiveConsole(code.InteractiveConsole):
    """Private. SuperInteractiveConsole properly emulates locals and globals when an InteractiveConsole is spawned."""
    def __init__(self, globals=None, locals=None, filename="<console>"):
        code.InteractiveConsole.__init__(self, locals=locals, filename=filename)
        self.globals = globals
    def runcode(self, codearg):
        try:
            exec codearg in self.globals, self.locals #modified to add support for globals
        except SystemExit:
            raise
        except:
            self.showtraceback()
        else:
            if code.softspace(sys.stdout, 0):
                print

def interact(globals=None, locals=None, banner="\nIn Python Interactive Loop. Enter Ctrl-Z to continue."):
    """Convience method to call SuperInteractiveConsole"""
    if globals is None:
        globals = globals()
    if locals is None:
        locals = locals()
    console = SuperInteractiveConsole(globals=globals, locals=locals)
    console.interact(banner)

def pdb():
    """Break into pdb"""
    import pdb
    pdb.set_trace()
    
def resumeThread(threadId):
    """Resumes a target thread"""
    THREAD_SUSPEND_RESUME = 0x0002
    hThread = kernel32.OpenThread(THREAD_SUSPEND_RESUME, False, threadId)
    kernel32.ResumeThread(hThread)
    kernel32.CloseHandle(hThread)

def debug_on_exception(func):
    func.debug_on_exception = True
    return func