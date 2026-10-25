@echo off
rem Quick check (small sizes only, about one minute). Run this before run_all.bat.
cd /d "%~dp0"
call run_all.bat --quick
