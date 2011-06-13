@echo off
set PWD=%CD%
set HERE=%~pd0
set PYTHON_TAR=Python-2.7.2.tar.bz2
set PYTHON_TAR_XFOLDER=Python-2.7.2
set PYTHON_URL=http://www.python.org/ftp/python/2.7.2/Python-2.7.2.tar.bz2

cd /d %HERE%

:get_python
if exist %PYTHON_TAR% goto extract_python
wget %PYTHON_URL%

:extract_python
if exist python goto set_vs9_env
tar -xf %PYTHON_TAR%
mv %PYTHON_TAR_XFOLDER% python

:set_vs9_env
setlocal
set pf=
if exist "%ProgramFiles(x86)%" set pf=%ProgramFiles(x86)%
if not exist "%pf%" set pf=%ProgramFiles%
set VS9=%pf%\Microsoft Visual Studio 9.0
endlocal & set VS9=%VS9%
if not exist "%VS9%\VC\vcvarsall.bat" goto novs9
call "%VS9%\VC\vcvarsall.bat"
goto build_python

:novs9
echo Visual Studio 9.0 (2008) was not found.
echo.

:build_python
cd python\PCBuild
if not exist python.exe call build.bat
if not exist python_d.exe call build.bat -d

:end
cd /d %PWD%
echo.
echo.
if exist python\PCBuild\python.exe echo python.exe sucessfully created
if not exist python\PCBuild\python.exe echo python.exe was not sucessfully created
if exist python\PCBuild\python_d.exe echo python_d.exe sucessfully created
if not exist python\PCBuild\python_d.exe echo python_d.exe was not sucessfully created
echo.