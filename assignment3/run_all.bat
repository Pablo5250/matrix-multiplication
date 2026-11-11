@echo off
rem Full study on Windows: double-click this file, or run it from a terminal.
rem Close other heavy programs and keep the laptop plugged in while it runs.
cd /d "%~dp0"

set PY=python
where python >nul 2>nul || set PY=py

rem If java is not in PATH, use the JDK that IntelliJ downloads to %USERPROFILE%\.jdks
where javac >nul 2>nul
if errorlevel 1 if not defined JAVA_HOME for /d %%D in ("%USERPROFILE%\.jdks\*") do set "JAVA_HOME=%%D"

echo Installing Python dependencies (psutil, matplotlib)...
%PY% -m pip install --user -r requirements.txt || goto :fail

%PY% run_all.py %*
if errorlevel 1 goto :fail
echo.
echo Finished. Look at the results\ and figures\ folders.
pause
exit /b 0

:fail
echo.
echo Something failed - read the message above.
pause
exit /b 1
