from ctypes import *

CHAR = c_char
BYTE = c_ubyte
WORD = c_ushort
DWORD = c_ulong
LONG = c_long

HANDLE = c_void_p

LPSTR = POINTER(CHAR)
LPBYTE = POINTER(BYTE)

HANDLE = c_void_p

class LUID(Structure):
	_fields_ = [
		('LowPart', DWORD),
		('HighPart', LONG),
	]

class LUID_AND_ATTRIBUTES(Structure):
	_fields_ = [
		('Luid', LUID),
		('Attributes', DWORD),
	]
assert sizeof(LUID_AND_ATTRIBUTES) == 12, sizeof(LUID_AND_ATTRIBUTES)
assert alignment(LUID_AND_ATTRIBUTES) == 4, alignment(LUID_AND_ATTRIBUTES)

class TOKEN_PRIVILEGES(Structure):
	_fields_ = [
		('PrivilegeCount', DWORD),
		('Privileges', LUID_AND_ATTRIBUTES * 1),
	]


kernel32 = windll.kernel32

NULL = None

class STARTUPINFOA(Structure):
	_fields_ = [
		('cb', DWORD), #structure size in bytes
		('lpReserved', LPSTR), #must be NULL
		('lpDesktop', LPSTR), #desktop. can be NULL
		('lpTitle', LPSTR), #Console title. can be NULL
		('dwX', DWORD), #position of window - ignored if STARTF_USEPOSITION not specified
		('dwY', DWORD), #position of window - ignored if STARTF_USEPOSITION not specified
		('dwXSize', DWORD), #size of window - ignored if STARTF_USEPOSITION not specified
		('dwYSize', DWORD), #size of window - ignored if STARTF_USEPOSITION not specified
		('dwXCountChars', DWORD), #console screen buffer size if STARTF_USECOUNTCHARS
		('dwYCountChars', DWORD), #console screen buffer size if STARTF_USECOUNTCHARS
		('dwFillAttribute', DWORD), #console colors if STARTF_USEFILLATTRIBUTE
		('dwFlags', DWORD), #various flags. 0 is fine.
		('wShowWindow', WORD), #if STARTF_USESHOWWINDOW
		('cbReserved2', WORD), #must be 0
		('lpReserved2', LPBYTE), #must be 0
		('hStdInput', HANDLE), #ignored if not STARTF_USESTDHANDLES
		('hStdOutput', HANDLE), #ignored if not STARTF_USESTDHANDLES
		('hStdError', HANDLE), #ignored if not STARTF_USESTDHANDLES
	]
assert sizeof(STARTUPINFOA) == 68, sizeof(STARTUPINFOA)
assert alignment(STARTUPINFOA) == 4, alignment(STARTUPINFOA)

class PROCESS_INFORMATION(Structure):
	_fields_ = [
		('hProcess', HANDLE),
		('hThread', HANDLE),
		('dwProcessId', DWORD),
		('dwThreadId', DWORD),
	]
assert sizeof(PROCESS_INFORMATION) == 16, sizeof(PROCESS_INFORMATION)
assert alignment(PROCESS_INFORMATION) == 4, alignment(PROCESS_INFORMATION)

PROCESS_ALL_ACCESS = 0x1F0FFF
PAGE_EXECUTE_READWRITE = 0x40
MEM_COMMIT = 0x1000
MEM_RELEASE = 0x8000
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x00000020

WAIT_FAILED = 0xFFFFFFFF
WAIT_TIMEOUT = 258
