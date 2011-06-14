The :mod:`pydetour` Module
--------------------------

This module is the C++ component of pyhack. It manages the raw creation of the detours, as well as other useful modules.

pydetour        :   zzzz

pydetour.memory :   Instance of the pydetour.memoryType type. This is an object that represents the entire
                    virtual address space of the process. It's most important ability is that indexing it returns
                    a copy of itself, with it's internal `base` attribute set to it's index (plus the old `base`).
                    
                    Some examples might be easier to understand::
                    
                        #Assuming memory looks like this:
                        
                        #0x04000000 = 0x05000000
                        #0x05000000 = 0x06000000
                        #0x05000004 = 0xFFFFFFFF
                        #0x06000000 = 0x00000042
                        
                    >>> from pydetour import memory as m
                    >>> m[0x04000000]
                    <memory object based at 0x04000000, autoInc False>
                    >>> m[0x04000000].dword()
                    0x05000000
                    >>> m[0x04000000].pointer()
                    <memory object based at 0x05000000, autoInc False>
                    >>> m[0x04000000].pointer().dword()
                    0x06000000
                    >>> m[0x04000000] >> 0 #Right shift 0 == pointer()
                    <memory object based at 0x05000000, autoInc False>
                    >>> m[0x04000000] >> 4 #You can also add an offset
                    <memory object based at 0x05000004, autoInc False>
                    >>> (m[0x04000000] >> 4).dword()
                    0xFFFFFFFF