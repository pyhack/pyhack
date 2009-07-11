import common_detours

class PatchManager(dict):
    """PatchManager is a class that managers a group of detours. It's keys are strings, and it's values are Patch instances"""
    def addCommonPatch(self, name):
        x = common_detours.getPatch(name)
        self[name] = x
        return x