from __future__ import with_statement

from symbol_resolver import SymbolResolver, SymbolNotDefinedException
from code import interact
import logging
log = logging.getLogger(__name__)

class MapFileSymbolResolver(SymbolResolver):
    def init(self, filename, seg_offset, seg_num='0001'):
        self.symbols_name = {}
        self.symbols_addr = {}
        self.seg_offset = seg_offset
        try:
            with open(filename) as f:
                map = _MapFileParser(f)
                map.check_duplicates()
            for addr, name in map.segments[seg_num]['symbols'].iteritems():
                self.symbols_name[name] = addr + seg_offset
                self.symbols_addr[addr + seg_offset] = name
        except IOError, e:
            log.exception("Could not read MAP file, symbols may be unavailable.")

    def resolve(self, name, *args, **kwargs):
        try:
            return self.symbols_name[name]
        except KeyError:
            try:
                return self.symbols_name[name.replace("::", "__")] + self.seg_offset
            except KeyError:
                raise SymbolNotDefinedException("The symbol '%s' was not defined"%(name))
        
    def reverse(self, addr, *args, **kwargs):
        try:
            return self.symbols_addr[addr]
        except KeyError:
            if not isinstance(addr, int):
                raise TypeError("'%s' is not an integer."%(addr))
            raise SymbolNotDefinedException("The address '%#x' does not have a symbolic name"%(addr))
        
class _MapFileParser():
    def __init__(self, input_gen):
        self.state = "begin"
        self.segments = {}
        for line in input_gen:
            if line == "\n":
                continue
            if line[0] == "#":
                continue
            if line[-1] == "\n":
                line = line[:-1]
            if self.state:
                getattr(self, 'parse_line_%s'%(self.state))(line)
            
    def parse_line_begin(self, line):
        if line == " Start         Length     Name                   Class":
            self.state = "segments"
            
    def parse_line_segments(self, line):
        if line == "  Address         Publics by Value":
            self.state = "symbols"
            return
        # 0001:00000000 00024D000H .text                  DATA
        parts = line.split()
        segnum = parts[0].split(":")[0]
        s = {
            'length': int(parts[1][:-1], 16),
            'name': parts[2] if len(parts) == 4 else '',
            'type': parts[3] if len(parts) == 4 else parts[2],
            'symbols': {}
        }
        self.segments[segnum] = s
            
    def parse_line_symbols(self, line):
        parts = line.split()
        if line.startswith("Program entry point at"):
            part = parts[-1]
            name = "entry"
            self.state = None
        else:
            part = parts[0]
            name = " ".join(parts[1:])
        segnum = part.split(":")[0]
        offset = int(part.split(":")[1], 16)
        self.segments[segnum]['symbols'][offset] = name
        
    def check_duplicates(self):
        all_symbols = {}
        for segnum, seg in self.segments.iteritems():
            for offs, name in seg['symbols'].iteritems():
                x = all_symbols.get(name, [])
                x.append((segnum, offs))
                all_symbols[name] = x
        for name, addrs in ((x,y) for x,y in all_symbols.iteritems() if len(y) > 1):
            for addr in addrs:
                log.warning("Duplicate symbol '%s' at %s:%#x"%(name, addr[0], addr[1]))

def _test():
    logging.basicConfig(level=logging.DEBUG)
    r = MapFileSymbolResolver(r"maptest.map", 0x00401000)
    interact(local=locals(), banner="r = r")
if __name__ == "__main__":
    _test()
