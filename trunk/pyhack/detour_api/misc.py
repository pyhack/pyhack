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
x = imp.get_suffixes()[0][0]
if x == "_d.pyd":
	pythonDebug = True


class SuperInteractiveConsole(code.InteractiveConsole):
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
	if globals is None:
		globals = globals()
	if locals is None:
		locals = locals()
	console = SuperInteractiveConsole(globals=globals, locals=locals)
	console.interact(banner)

def pdb():
	pdb.set_trace()