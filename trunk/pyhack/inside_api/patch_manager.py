import pprint

class PluginManager(dict):
    """PluginManager is a class that manages a group of plugins. It's keys are strings, and it's values are `Plugin` instances"""
    def __repr__(self):
        return pprint.pformat(dict(self))
    def __getattr__(self, key):
        if key in self:
            return self[key]
    def __setattr__(self, key, val):
        self[key] = val