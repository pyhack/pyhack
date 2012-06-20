r"""
:mod:`launcher_api.launcher` module
---------------------------------------

The :mod:`pyhack.launcher_api.launcher` module contains the :class:`TargetLauncher`
class used for establishing a target to run and the APP configuration for
the injected PyDetour module.


.. autoclass:: TargetLauncher(object)
    :members: __init__
    :undoc-members:
    :inherited-members:
      
    *Parameters*:
     * *dll : The path to the PyDetour module*
     * *pyHome : The path to the PyHack module*
     * *targetDef : A dictionary describing a target*
     
.. autoclass:: TargetLaunchException(Exception)
    :members:
    
    .. automethod:: __init__(self, retVal, message)
"""

import os
import sys
import logging
import pickle

log = logging.getLogger(__name__)

from pyhack.util.defines import *
from process import Process

from pyhack.util.paths import Paths

class TargetLaunchException(Exception):
    def __init__(self, retVal, message):
        super(TargetLaunchException, self).__init__(retVal, message)
        self.message = message

class TargetLauncher(object):
    CREATION_PAUSE = 1
    ALLOC_ALLOCATED = 2
    REMOTE_THREAD_RETURN = 3
    ALLOC_BEFORE_FREE = 4
    
    LAUNCHMETHOD_CREATE_REMOTE_THREAD = 1 #Broken
    LAUNCHMETHOD_DOUBLE_APC = 2

    #Error codes are 32-bit values (bit 31 is the most significant bit).
    #Bit 29 is reserved for application-defined error codes; no system error code has this bit set.
    #If you are defining an error code for your application, set this bit to one.
    #
    #Source: http://msdn.microsoft.com/en-us/library/ms679360%28VS.85%29.aspx
    BIT_29 = (1 << 29)
    ERROR_CODES = {
        0:                 ["success",             "Success"],
        BIT_29 + 1:         ["ll_failed",             "Remote thread failed LoadLibrary()"],
        BIT_29 + 2:         ["gpc_failed",             "Remote thread failed GetProcAddress() for dll function"],
        
        #The ones below here are returned from pydetour dll function, not from our ASM
        BIT_29 + 3:         ["rp_fail_read",        "Remote python function failed reading python file"],
        BIT_29 + 4:         ["re_fail_exception",    "Remote python function encountered an exception in python file"],
        
        #Weird stuff
        536870918:        ["pdb_c",                "Exception occured in remote python function, PDB chose to continue"],
        3221225786:     ["console_closed",         "Remote console window closed or other scary error"],
    }
    ERROR_CODES_NAMED = {}
    for k, v in ERROR_CODES.iteritems():
        ERROR_CODES_NAMED[v[0]] = k
        
    def __init__(self, dll, pyHome, targetDef, mode='start'):
        """Initialize `TargetLauncher` with a dll path, the pyHome path, and a targetDef."""
        self.dll = dll
        self.pyHome = pyHome
        self.targetDef = targetDef
    
    @staticmethod
    def _enableDebugPrivilege():
        log.debug("Enabling SeDebugPrivilege")
        Process().token.enableDebugPrivilege()
    
    def _launcher_environ_config(self):
        """Setup Paths in environment.
        
        - Add path to pyHome so CreateProcess() can find python26_d.
        - Add environ var pyHack_ParentPath pointing to a directory above the pyHack package.
        - Add environ var pyHack_Config which is a pickled configuration.
        
        pyHack_ParentPath is required because when unpickling the pyHack_Config, pickle needs to
        be able to find pyhack on the path.
        """
        
        home_dll_path = self.pyHome
        
        if 'PCbuild' in os.listdir(home_dll_path):
            home_dll_path = os.path.join(home_dll_path, "PCbuild")
        
        log.debug(home_dll_path)
        p = os.environ['PATH'].split(";")
        p.append(home_dll_path)
        os.environ['PATH'] = ';'.join(p)
        
        conf = {
            'dll': self.dll,
            'pyHome': self.pyHome,
            'targetDef': self.targetDef,
        }
        os.environ['pyHack_ParentPath'] = Paths.trunk
        os.environ['pyHack_Config'] = pickle.dumps(conf)

    def launch(self):
        """This is a simplified interface for `TargetLauncher._launch_process` that assumes a CLI is available."""
        for step, args in self.launch_process(TargetLauncher.LAUNCHMETHOD_DOUBLE_APC):
            if step == TargetLauncher.CREATION_PAUSE:
                p = args[0]
                #log.info("Attach debugger now, and press enter to continue")
                #raw_input()
            if step == TargetLauncher.REMOTE_THREAD_RETURN:
                retVal = args[0]
                
        log.info("Remote thread return value: %d"%(retVal))
        if retVal == 0:
            return p
        e = "Scary Unknown Error in remote thread (%s)"%(retVal)
        if retVal in TargetLauncher.ERROR_CODES:
            e = TargetLauncher.ERROR_CODES[retVal][1]
        log.error(e)
        raise TargetLaunchException(retVal, e)
        return retVal
        
    def launch_process(self, method):
        """This function is a generator. Each time it is resumed, another step in launching the process occurs."""
        if method not in (
            TargetLauncher.LAUNCHMETHOD_CREATE_REMOTE_THREAD,
            TargetLauncher.LAUNCHMETHOD_DOUBLE_APC,
            ):
            raise Exception("Invalid Launch Method")
            
        targetDef = self.targetDef

        self._enableDebugPrivilege()

        self._launcher_environ_config()

        p = Process.create(targetDef.exe, targetDef.args, targetDef.startIn, suspended=True)
        log.info("Spawned target, pid %d, main thread id %s"%(p.pid, p._idMainThread))
        
        yield (TargetLauncher.CREATION_PAUSE, (p, ))

        if method == TargetLauncher.LAUNCHMETHOD_DOUBLE_APC:
            log.info("Creating injection stubs")
            parent_wait_event = r"Local\pyhack_parent_wait"
            child_wait_event = r"Local\pyhack_child_wait"
            alloc = self._createInjectedStubs_doubleapc(self.dll, p.memory, parent_wait_event, child_wait_event)
            yield (TargetLauncher.ALLOC_ALLOCATED, (alloc, ))
            
            import ctypes
            parent_evt = ctypes.windll.kernel32.CreateEventA(0,0,0,parent_wait_event)
            child_evt = ctypes.windll.kernel32.CreateEventA(0,0,0,child_wait_event)
            log.info("Starting APC")
            p.queueAPC(alloc['executionPoint']+1)
            p.resume()
        
            raw_input("Press enter to continue child process (beginning of first APC)")
            ctypes.windll.kernel32.SetEvent(child_evt)
            
            print "Waiting for child to initialize"
            ctypes.windll.kernel32.WaitForSingleObject(parent_evt, 0xFFFFFFFF)

            p._mainsuspend()
            #raw_input("Press enter to continue child process (main thread)")
            ctypes.windll.kernel32.SetEvent(child_evt)
            
            ctypes.windll.kernel32.CloseHandle(child_evt)
            ctypes.windll.kernel32.CloseHandle(parent_evt)
            retVal = 0
            
        elif method == TargetLauncher.LAUNCHMETHOD_CREATE_REMOTE_THREAD:
            log.info("Creating injection stub")
            alloc = self._createInjectedStubs_remote_thread(self.dll, p.memory)
            
            yield (TargetLauncher.ALLOC_ALLOCATED, (alloc, ))
            
            log.info("Creating remote thread")
            retVal = p.createRemoteThreadWait(alloc['executionPoint']+1)

        yield (TargetLauncher.REMOTE_THREAD_RETURN, (retVal, ))
        
        yield (TargetLauncher.ALLOC_BEFORE_FREE, (alloc, ))
        
        log.info("Not freeing memory")  #Freeing memory is dangerous as there is still code running if the thread has been re-suspended via double apc method
        for name, addr in alloc.iteritems():
            log.debug("Didn't free 0x%x (%s)"%(addr, name))
        #    p.memory.free(a)

    def _createInjectedStubs_doubleapc(self, dll, mem, parent_wait, child_wait):
        """Allocate memory, create an ASM stub, copy strings and code into the target.
        
        This stub has five goals:
        - AllocConsole: This gives us a new console in the target process.
        - LoadLibraryA: This is used to load the pydetour dll into the process.
        - GetProcAddress: This is used to find our target exported function from within the above DLL.
        - Launch python code: Call the exported function, passing the path of the bootstrap function.
        - Replace entry point with the bytes we grabbed
        - Return exit status (?somehow)
        
        This function returns a dictionary of allocation points in the remote process.
        
        High level description of ASM function::
        
            def InjectedStub():
                kernel32.AllocConsole()
                hModule = kernel32.LoadLibraryA(dll)
                if not hModule:
                    ExitThread(errors['ll_failed'])
                rpf = kernel32.GetProcAddress(hModule, "run_python_file")
                if not rpf:
                    ExitThread(errors['gpc_failed'])
                ret = rpf(Paths.inside_bootstrap_py)
                return
        """
        errors = TargetLauncher.ERROR_CODES_NAMED

        alloc = {}
        alloc['pyPath'] = mem.allocWrite(Paths.inside_bootstrap_py)
        alloc['dllPath'] = mem.allocWrite(dll)
        alloc['dllFunc'] = mem.allocWrite("run_python_file")
        alloc['parent_wait'] = mem.allocWrite(parent_wait)
        alloc['child_wait'] = mem.allocWrite(child_wait)
        alloc['executionPoint'] = mem.alloc(None, 256)
        alloc['secondAPC'] = mem.alloc(None, 256)
        hM = kernel32.GetModuleHandleA("kernel32.dll")
        hM_ntdll = kernel32.GetModuleHandleA("ntdll.dll")

        from util.buffer import ASMBuffer
        
        if True:
            #This stub is the /second/ apc to run
            buf = ASMBuffer(256)
            #---------------------------------------------------------------------
            #---------------------------------------------------------------------
            #---------------------------------------------------------------------
            buf.callEAX(kernel32.GetProcAddress(hM, "AllocConsole"))
            
            #---------------------------------------------------------------------
            buf.pushAddr(alloc['dllPath'])
            buf.callEAX(kernel32.GetProcAddress(hM, "LoadLibraryA")) #hModule to dll -> EAX
            buf.cmpEAX_Byte(0x0)
            buf.namedJNZ("ll_success")

            if True:
                buf.callEAX(kernel32.GetProcAddress(hM, "GetLastError"))
                buf.INT3()
                #buf.pushEAX()
                buf.pushDword(errors['ll_failed']) #PUSH 0x1 (thread exit code) 1 = LoadLibrary Failed
                #buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
                buf.popEAX()
                buf.namedJMP("exit")

            #---------------------------------------------------------------------
            buf.nameTarget("ll_success")
            buf.pushAddr(alloc['dllFunc'])
            buf.pushEAX()    #PUSH EAX (hModule to dll)
            buf.callEAX(kernel32.GetProcAddress(hM, "GetProcAddress"))
            buf.cmpEAX_Byte(0x0)
            buf.namedJNZ("gpa_success")

            if True:
                buf.INT3()
                buf.pushDword(errors['gpc_failed']) #PUSH thread exit code 'GetProcAddress Failed'
                #buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
                buf.popEAX()
                buf.namedJMP("exit")

            #---------------------------------------------------------------------
            buf.nameTarget("gpa_success")
            buf.pushAddr(1) #turns on pdb debugging
            buf.pushAddr(alloc['pyPath'])
            buf.callEAX() #This calls our run_python_code script
            buf.addESP(8)
            buf.cmpEAX_Byte(0x0)
            buf.namedJZ("run_success")

            if True:
                buf.INT3()
                #run_python_code failed, return it's error code
                buf.pushEAX()
                #buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
                buf.popEAX()
                buf.namedJMP("exit")
            
            #---------------------------------------------------------------------
            buf.nameTarget("run_success")
            buf.nameTarget("exit", allowFlowThrough=True)
            
            self._asmbuf_setevent(buf, hM, alloc['parent_wait']) #Tell the parent to go ahead
            self._asmbuf_waitevent(buf, hM, alloc['child_wait']) #Wait until parent gives us the go ahead
           
            buf.ret(3*4) #APC is passed 3 params
           
            buf.push([0xCC, 0xCC, 0xCC, 0xCC, 0xCC]) #Debugger trap
            buf.push([0xCC, 0xCC, 0xCC, 0xCC, 0xCC]) #Debugger trap


            
            buf.verifyJumps()
            log.debug("Second APC stub is %s bytes."%(buf.cursor))
            mem.write(alloc['secondAPC'], buf.buf.raw)
        
        if True:
            #This stub is the /first/ apc to run
            #---------------------------------------------------------------------
            #---------------------------------------------------------------------
            from util.buffer import ASMBuffer
            bufapc = ASMBuffer(256)
            bufapc.INT3() #This is skipped over by scheduling the first apc at +1
            self._asmbuf_waitevent(bufapc, hM, alloc['child_wait']) #Wait until the parent gives us the go ahead
            bufapc.pushDword(0)
            bufapc.pushDword(0)
            bufapc.pushDword(0)
            bufapc.pushAddr(alloc['secondAPC'])
            bufapc.callEAX(kernel32.GetProcAddress(hM, "GetCurrentThread"))
            bufapc.pushEAX()
            bufapc.callEAX(kernel32.GetProcAddress(hM_ntdll, "NtQueueApcThread"))
            bufapc.ret(3*4)
            mem.write(alloc['executionPoint'], bufapc.buf.raw)

        return alloc
    @staticmethod
    def _asmbuf_waitevent(asmbuf, k32_hm, evt_name_address):
        asmbuf.pushAddr(evt_name_address)
        asmbuf.pushDword(0)
        asmbuf.pushDword(0)
        asmbuf.pushDword(0)
        asmbuf.callEAX(kernel32.GetProcAddress(k32_hm, "CreateEventA"))
        asmbuf.pushEAX() #Used later by CloseHandle
        asmbuf.pushDword(0xFFFFFFFF)
        asmbuf.pushEAX()
        asmbuf.callEAX(kernel32.GetProcAddress(k32_hm, "WaitForSingleObject"))
        asmbuf.callEAX(kernel32.GetProcAddress(k32_hm, "CloseHandle"))
    @staticmethod
    def _asmbuf_setevent(asmbuf, k32_hm, evt_name_address):
        asmbuf.pushAddr(evt_name_address)
        asmbuf.pushDword(0)
        asmbuf.pushDword(0)
        asmbuf.pushDword(0)
        asmbuf.callEAX(kernel32.GetProcAddress(k32_hm, "CreateEventA"))
        asmbuf.pushEAX() #Used later by CloseHandle
        asmbuf.pushEAX() #Used by SetEvent
        asmbuf.callEAX(kernel32.GetProcAddress(k32_hm, "SetEvent"))
        asmbuf.callEAX(kernel32.GetProcAddress(k32_hm, "CloseHandle"))
    def _createInjectedStubs_remote_thread(self, dll, mem):
        """Allocate memory, create an ASM stub, copy strings and code into the target and executed via CreateRemoteThread().
        
        This stub has five goals:
        - AllocConsole: This gives us a new console in the target process.
        - LoadLibraryA: This is used to load the pydetour dll into the process.
        - GetProcAddress: This is used to find our target exported function from within the above DLL.
        - Launch python code: Call the exported function, passing the path of the bootstrap function.
        - Return exit status via ExitThread.
        
        This function returns a dictionary of allocation points in the remote process.
        
        High level description of ASM function::
        
            def InjectedStub():
                kernel32.AllocConsole()
                hModule = kernel32.LoadLibraryA(dll)
                if not hModule:
                    ExitThread(errors['ll_failed'])
                rpf = kernel32.GetProcAddress(hModule, "run_python_file")
                if not rpf:
                    ExitThread(errors['gpc_failed'])
                ret = rpf(Paths.inside_bootstrap_py)
                ExitThread(ret)
        """
        errors = TargetLauncher.ERROR_CODES_NAMED

        alloc = {}
        alloc['pyPath'] = mem.allocWrite(Paths.inside_bootstrap_py)
        alloc['dllPath'] = mem.allocWrite(dll)
        alloc['dllFunc'] = mem.allocWrite("run_python_file")
        alloc['executionPoint'] = mem.alloc(None, 128) #we need about 123 bytes
        hM = kernel32.GetModuleHandleA("kernel32.dll")

        from util.buffer import ASMBuffer
        buf = ASMBuffer(128)

        #buf.INT3() #Debugger trap
        
        #---------------------------------------------------------------------
        buf.movEAX_Addr(kernel32.GetProcAddress(hM, "AllocConsole"))
        buf.callEAX() #AllocConsole()
        
        #---------------------------------------------------------------------
        buf.pushAddr(alloc['dllPath'])
        buf.movEAX_Addr(kernel32.GetProcAddress(hM, "LoadLibraryA"))
        buf.callEAX() #hModule to dll -> EAX
        buf.cmpEAX_Byte(0x0)
        buf.namedJNZ("ll_success")

        if True:
            #buf.movEAX_Addr(kernel32.GetProcAddress(hM, "GetLastError"))
            #buf.callEAX() #GetLastError
            #buf.pushEAX()
            buf.pushDword(errors['ll_failed']) #PUSH 0x1 (thread exit code) 1 = LoadLibrary Failed
            buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
            buf.callEAX() #This cleanly exits the thread    

        #---------------------------------------------------------------------
        buf.nameTarget("ll_success")
        buf.pushAddr(alloc['dllFunc'])
        buf.pushEAX()    #PUSH EAX (hModule to dll)
        buf.movEAX_Addr(kernel32.GetProcAddress(hM, "GetProcAddress"))
        buf.callEAX() #dllFunc() address -> EAX
		
        buf.cmpEAX_Byte(0x0)
        buf.namedJNZ("gpa_success")

        if True:
            buf.pushDword(errors['gpc_failed']) #PUSH thread exit code 'GetProcAddress Failed'
            buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
            buf.callEAX() #This cleanly exits the thread

        #---------------------------------------------------------------------
        buf.nameTarget("gpa_success")
        buf.pushAddr(1) #turns on pdb debugging
        buf.pushAddr(alloc['pyPath'])
        buf.callEAX() #This calls our run_python_code script
        buf.addESP(8)
        buf.cmpEAX_Byte(0x0)
        buf.namedJZ("run_success")

        if True:
            #run_python_code failed, return it's error code
            buf.pushEAX()
            buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
            buf.callEAX() #This cleanly exits the thread
        
        #---------------------------------------------------------------------
        buf.nameTarget("run_success")
        
        #buf.INT3()
        
        buf.pushByte(0) #PUSH 0x0 (thread exit code, success)
        buf.movEAX_Addr(kernel32.GetProcAddress(hM, "ExitThread"))
        buf.callEAX() #This cleanly exits the thread
        
        
        buf.push([0xCC, 0xCC, 0xCC, 0xCC, 0xCC]) #Debugger trap
        buf.push([0xCC, 0xCC, 0xCC, 0xCC, 0xCC]) #Debugger trap
        
        buf.verifyJumps()
        log.debug("Stub is %s bytes."%(buf.cursor))
        mem.write(alloc['executionPoint'], buf.buf.raw)
        
        return alloc
