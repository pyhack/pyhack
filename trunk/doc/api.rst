The :mod:`pyhack` API
---------------------

The PyHack module is broken into three component parts. 

1. PyDetour  :   A native Window's module containing a majority of the internal
                 injection machinery. This module is not typically the interest
                 of PyHack users, directly.
2. launch_api:   The launch_api is specifically used for developing customized
                 launching applications and scripts. The official launcher, 
                 Bones, uses this API extensively.
3. inside_api:   Associated Patcher Plugins use this API for manipulating the
                 target once PyDetour has established the injected hooks.

.. toctree::
   :maxdepth: 2

   launch_api
   util

