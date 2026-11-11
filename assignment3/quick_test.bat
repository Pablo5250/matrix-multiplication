@echo off
rem Quick check (small sizes only, about two minutes). Run this before run_all.bat.
cd /d "%~dp0"
call run_all.bat --quick
