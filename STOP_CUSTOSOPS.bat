@echo off
setlocal
cd /d "%~dp0"
powershell.exe -ExecutionPolicy Bypass -File "%~dp0scripts\stop-custosops.ps1"
pause
endlocal