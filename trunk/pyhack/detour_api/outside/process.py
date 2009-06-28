"""This file holds utility classes used by the launcher. It is generally /not/ included inside the target's process"""
from ctypes import *

from util.defines import *

import logging
log = logging.getLogger("process")

class Process(object):
	log = logging.getLogger("process.Process")
	def __init__(self):
		self.pid = kernel32.GetCurrentProcessId()
		self.hProcess = kernel32.GetCurrentProcess()
		self._hMainThread = None
		self._idMainThread = None
	def __del__(self):
		if self.hProcess:
			kernel32.CloseHandle(self.hProcess)
		if self._hMainThread:
			kernel32.CloseHandle(self._hMainThread)
	def getMemory(self):
		if hasattr(self, "_memory"):
			return self._memory
		self._memory = VirtualMemory(self)
		return self._memory
	memory = property(getMemory)
	def getToken(self):
		if hasattr(self, "_processToken"):
			return self._processToken
		self._processToken = ProcessToken(self)
		return self._processToken
	token = property(getToken)
	def suspend(self):
		log.error("Process.suspend() is not yet implemented")
		raise NotImplementedError
	def resume(self):
		kernel32.ResumeThread(self._hMainThread)
	def terminate(self):
		kernel32.TerminateProcess(self.hProcess, 0)
	def getExitCode(self):
		ec = DWORD(0)
		s = kernel32.GetExitCodeProcess(self.hProcess, byref(ec))
		if s == 0:
			raise WinError()
		return ec
	def createRemoteThreadWait(self, address):
		log.debug("Calling CreateRemoteThread on hProcess %s @ 0x%X"%(self.hProcess, address))
		threadId = DWORD()
		s = kernel32.CreateRemoteThread(self.hProcess, 0, 0, address, 0, 0, 0)
		if s == 0: raise WinError()
		hThread = s
		log.debug("Waiting for thread to complete")
		s = None
		while s != 0:
			s = kernel32.WaitForSingleObject(hThread, 0xFF)
			if s == 0xFFFFFFFF: raise WinError() #WAIT_FAILED
		retStatus = DWORD()
		s = kernel32.GetExitCodeThread(hThread, byref(retStatus))
		if s == 0: raise WinError()
		kernel32.CloseHandle(hThread)
		log.debug("Got thread exit code %i"%(retStatus.value))
		return retStatus.value
	@classmethod
	def open(cls, pid=None):
		"""Opens an existing process. Returns new Process object."""
		o = cls()
		if pid is None:
			return o #default constructor opens self
		access = PROCESS_ALL_ACCESS
		hProcess = kernel32.OpenProcess(access, 0, pid)
		if hProcess == 0:
			raise WinError()
		o.pid = pid
		o.hProcess = hProcess
		return cls
	@classmethod
	def create(cls, exe="", args="", startDir="", suspended=True):
		"""Creates a process. Returns new Process object."""
		CREATE_SUSPENDED = 0x00000004
		CREATE_NEW_CONSOLE = 0x00000010

		createFlags = 0
		if suspended:
			createFlags = createFlags | CREATE_SUSPENDED | CREATE_NEW_CONSOLE

		si = STARTUPINFOA()
		si.cb = sizeof(si)
		pi = PROCESS_INFORMATION()

		ret = kernel32.CreateProcessA(
			exe,
			args,
			NULL,
			NULL,
			1,
			createFlags,
			NULL,
			startDir,
			byref(si),
			byref(pi)
		)
		if ret == 0:
			raise WinError()
		o = cls()
		o._hMainThread = pi.hThread
		print dir(pi)
		o._idMainThread = pi.dwThreadId # windll.kernel32.GetThreadId(o._hMainThread)
		o.hProcess = pi.hProcess
		o.pid = pi.dwProcessId
		return o


class VirtualMemory(object):
	log = logging.getLogger("process.VirtualMemory")
	def __init__(self, p):
		if not isinstance(p, Process):
			raise ValueError("p must be a valid Process Instance")
		self.process = p
	def protect(self, addr, bytes, protection):
		log.debug("protect(0x%H, 0xH bytes)"%(addr, bytes))
		oldProt = DWORD()
		s = kernel32.VirtualProtectEx(
			self.process.hProcess,
			addr,
			bytes,
			PAGE_EXECUTE_READWRITE,
			byref(oldProt)
		)
		if s == 0: raise WinError()
		return oldProt.value
	def alloc(self, addr=None, bytes=0):
		log.debug("alloc(0x%X bytes)"%(bytes))
		s = kernel32.VirtualAllocEx(
			self.process.hProcess,
			addr,
			bytes,
			MEM_COMMIT,
			PAGE_EXECUTE_READWRITE,
		)
		if s == 0: raise WinError()
		log.debug("allocated at 0x%X"%(s))
		return s
	def allocWrite(self, bytestring):
		a = self.alloc(None, len(bytestring) + 1)
		self.write(a, bytestring + "\0") #for safety - NULL
		return a
	def free(self, addr):
		log.debug("free(0x%X)"%(addr))
		s = kernel32.VirtualFreeEx(
			self.process.hProcess,
			addr,
			0,
			MEM_RELEASE
		)
		if s == 0: raise WinError()
	def write(self, addr, bytestring):
		lstr = ''.join((str(x) for x in bytestring if ord(x) < 128))
		log.debug("write(0x%X, '%s')"%(addr, lstr))
		if not isinstance(bytestring, str):
			raise ValueError("bytestring must be a real python byte string")
		bytesWritten = DWORD()
		s = kernel32.WriteProcessMemory(
			self.process.hProcess,
			addr,
			bytestring,
			len(bytestring),
			byref(bytesWritten),
		)
		if s == 0: raise WinError()
		assert bytesWritten.value == len(bytestring)
	def read(self, addr, bytes):
		b = create_string_buffer(bytes)
		bytesRead = DWORD()
		s = kernel32.ReadProcessMemory(
			self.process.hProcess,
			addr,
			byref(b),
			bytes,
			byref(bytesRead)
		)
		if s == 0: raise WinError()
		assert bytesRead.value == bytes
		return b.raw

class ProcessToken(object):
	def __init__(self, p):
		if not isinstance(p, Process):
			raise ValueError("p must be a valid Process Instance")
		self.process = p
		self.hToken = self._openProcessToken()

	def __del__(self):
		if self.hToken:
			kernel32.CloseHandle(self.hToken)

	def _openProcessToken(self):
		hToken = HANDLE()
		s = windll.advapi32.OpenProcessToken(self.process.hProcess, TOKEN_ADJUST_PRIVILEGES, byref(hToken))
		if s == 0: raise WinError()
		return hToken

	@staticmethod
	def lookupPrivilegeValue(privName):
		luid = LUID()
		s = windll.advapi32.LookupPrivilegeValueA(0, privName, byref(luid))
		if s == 0: raise WinError()
		return luid

	def adjustPrivilege(self, privName, enabled):
		luid = self.lookupPrivilegeValue(privName)

		token_state = TOKEN_PRIVILEGES()
		token_state.PrivilegeCount = 1
		token_state.Privileges[0].Luid = luid
		token_state.Privileges[0].Attributes = 0
		if enabled:
			token_state.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

		s = windll.advapi32.AdjustTokenPrivileges(self.hToken, 0, byref(token_state), 0, 0, 0)
		if s == 0: raise WinError()
	def enableDebugPrivilege(self):
		self.adjustPrivilege("seDebugPrivilege", True)