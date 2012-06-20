class SymbolNotDefinedException(KeyError):
    pass
    


class SymbolResolver(object):
    SymbolNotDefinedException = SymbolNotDefinedException
    def __init__(self, *args, **kwargs):
        if hasattr(self, 'init'):
            self.init(*args, **kwargs)
            
    def resolve(self, name, *args, **kwargs):
        raise SymbolNotDefinedException("The symbol '%s' was not defined"%(name))
        
    def grep(self, t):
        r = self.find(t)
        for x, a in sorted(r.iteritems()):
            print "%0#8x:\t%s"%(a, x)
            
    def find(self, partialname):
        ret = {}
        import re
        partialname = re.escape(partialname)
        partialname = partialname.replace(r"\:\:", r"([:_])\1")
        partialname = partialname.replace(r"\?", r".?")
        partialname = partialname.replace(r"\*", r".*")
        pat = re.compile(".*%s.*"%(partialname), re.I)
        for name, addr in self.symbols_name.iteritems():
            if re.match(pat, name):
                ret[name] = addr
        return ret
        
    def find_re(self, partialname):
        ret = {}
        import re
        pat = re.compile(partialname, re.I)
        for name, addr in self.symbols_name.iteritems():
            if re.match(pat, name):
                ret[name] = addr
        return ret