@echo off
set ROOT=%~dp0
powershell.exe -ExecutionPolicy Bypass -File "%ROOT%scripts\stop-custosops.ps1"
if errorlevel 1 (
  echo.
  echo CustosOps stop command reported a problem. Check docs\onboarding\TROUBLESHOOTING.md.
  pause
)