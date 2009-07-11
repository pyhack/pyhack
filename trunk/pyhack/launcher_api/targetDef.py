_NOT_SET_STR = "PROPERTY_NOT_SET"


class TargetDefException(Exception):
    pass

class TooManyTargetsException(TargetDefException):
    pass
    

def makeTargets(all_target_dict):
    """Given a dict of target dicts, return a dict of targetDefs"""
    ret = {}
    for targetName, targetDict in all_target_dict.iteritems():
        ret[targetName] = TargetDef(targetName, targetDict)
    return ret

class TargetDef(object):
    """A TargetDef is a Target Definition. It locates a particular target on the local system."""
    def __init__(self, name=None, init_dict=None):
        self.name = _NOT_SET_STR
        self.exe = _NOT_SET_STR
        self.startIn = _NOT_SET_STR
        self.args =  _NOT_SET_STR
        self.pycode = _NOT_SET_STR
        if init_dict is not None:
            self.fromDict(name, init_dict)

    def fromDict(self, name, in_dict):
        self.name = name
        self.exe = in_dict['exe']
        self.startIn = in_dict['startIn']
        self.args = in_dict['args']
        self.pycode = in_dict['pycode']

    def __str__(self):
        return "<TargetDef for '%s'>"%(self.name)
