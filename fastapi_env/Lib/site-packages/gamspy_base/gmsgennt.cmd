@echo off
gmsgennx.exe "%~4" %6
if not %ERRORLEVEL% == 0 echo ERROR: Solver %6 returned with nonzero exitcode %ERRORLEVEL% 1>&2
