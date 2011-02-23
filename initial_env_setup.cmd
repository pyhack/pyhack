@echo off
set PWD=%CD%
set HERE=%~pd0
set PYTHON_TAR=Python-2.7.1.tar.bz2
set PYTHON_TAR_XFOLDER=Python-2.7.1
set PYTHON_URL=http://www.python.org/ftp/python/2.7.1/Python-2.7.1.tar.bz2

cd /d %HERE%

:get_python
if exist %PYTHON_TAR% goto extract_python
wget %PYTHON_URL%

:extract_python
if exist python goto set_vs9_env
tar -xf %PYTHON_TAR%
mv %PYTHON_TAR_XFOLDER% python

:set_vs9_env
set VS9=%ProgramFiles(x86)%\Microsoft Visual Studio 9.0
call "%VS9%\VC\vcvarsall.bat"
set VS9=%ProgramFiles%\Microsoft Visual Studio 9.0
call "%VS9%\VC\vcvarsall.bat"

:build_python
cd python\PCBuild
call build.bat
call build.bat -d

:end
cd /d %PWD%