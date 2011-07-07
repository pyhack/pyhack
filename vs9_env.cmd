@echo off
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
goto end

:novs9
echo Visual Studio 9.0 (2008) was not found.
echo.

:end
cd /d %PWD%
echo.
echo.