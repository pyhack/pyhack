@echo off
setlocal
set PWD=%CD%
set HERE=%~pd0

cd /d %HERE%

:set_vs9_env
setlocal
set pf=
if exist "%ProgramFiles(x86)%" set pf=%ProgramFiles(x86)%
if not exist "%pf%" set pf=%ProgramFiles%
set VS9=%pf%\Microsoft Visual Studio 9.0
endlocal & set VS9=%VS9%
if not exist "%VS9%\VC\vcvarsall.bat" goto novs9
call "%VS9%\VC\vcvarsall.bat"
goto build_pyhack

:novs9
echo Visual Studio 9.0 (2008) was not found.
echo.

:build_pyhack
set PYTHON=%HERE%\python\PCBuild\python.exe
set PYTHON_D=%HERE%\python\PCBuild\python_d.exe
set PYTHON_SCRIPTS=%HERE%\python\Scripts
cd trunk
::Install pyhack in develop mode
"%PYTHON%" setup.py develop
::Install pyhack in develop mode (debug extension modules)
"%PYTHON%" setup.py build -g develop

:end
cd /d %PWD%
echo.
echo.