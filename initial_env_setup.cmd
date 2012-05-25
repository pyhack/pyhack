@echo off
setlocal
set PWD=%CD%
set HERE=%~pd0
set OLDPATH=%PATH%
set PYTHON_TAR=Python-2.7.2.tar.bz2
set PYTHON_TAR_XFOLDER=Python-2.7.2
set PYTHON_URL=http://www.python.org/ftp/python/2.7.2/Python-2.7.2.tar.bz2

set DISTRIBUTE_URL=http://python-distribute.org/distribute_setup.py

cd /d %HERE%

::Check for some cygwin commands we need
wget --version 2>NUL > NUL
IF ERRORLEVEL 1 GOTO :no_wget
tar --version 2>NUL > NUL
IF ERRORLEVEL 1 GOTO :no_tar
mv --version 2>NUL > NUL
IF ERRORLEVEL 1 GOTO :no_mv


goto get_python

:no_wget
echo.
echo wget not found, is it on the path?
echo You should install cygwin.
goto end

:no_tar
echo.
echo tar not found, is it on the path?
echo You should install cygwin.
goto end

:no_mv
echo.
echo mv not found, is it on the path?
echo You should install cygwin.
echo.
goto end

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
set PY_DIR=%CD%
set PYTHON=%CD%\python.exe
set PYTHON_D=%CD%\python_d.exe
cd /d %HERE%
set PYTHON_SCRIPTS=%HERE%\python\Scripts

:install_distribute
wget %DISTRIBUTE_URL%
"%PYTHON%" distribute_setup.py
del distribute_setup.py

:install_packages
"%PYTHON_SCRIPTS%\easy_install.exe" pip
"%PYTHON_SCRIPTS%\pip.exe" install virtualenv
"%PYTHON_SCRIPTS%\pip.exe" install sphinx

:create_pyhack_docs
cd /d %HERE%\trunk\doc
::sphinx batch needs this
set path=%HERE%\python\PCbuild;%HERE%\python\scripts;
call make.bat html

:end
cd /d %PWD%
echo.
echo.
if exist python\PCBuild\python.exe echo python.exe sucessfully created
if not exist python\PCBuild\python.exe echo python.exe was not sucessfully created
if exist python\PCBuild\python_d.exe echo python_d.exe sucessfully created
if not exist python\PCBuild\python_d.exe echo python_d.exe was not sucessfully created
echo.