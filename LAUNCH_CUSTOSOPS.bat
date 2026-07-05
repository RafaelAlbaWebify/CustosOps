@echo off
set ROOT=%~dp0
powershell.exe -ExecutionPolicy Bypass -File "%ROOT%scripts\launch-custosops.ps1"
if errorlevel 1 (
  echo.
  echo CustosOps launch failed. Read the message above, then check docs\onboarding\TROUBLESHOOTING.md.
  pause
)