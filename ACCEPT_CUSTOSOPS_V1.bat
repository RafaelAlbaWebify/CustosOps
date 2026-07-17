@echo off
set ROOT=%~dp0
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\run-v1-clean-machine-acceptance.ps1"
if errorlevel 1 (
  echo.
  echo CustosOps v1 clean-machine acceptance failed.
  echo Review the CUSTOSOPS_V1_ACCEPTANCE_FAILED ZIP in Downloads.
  exit /b 1
)
echo.
echo CustosOps v1 clean-machine acceptance completed successfully.
exit /b 0
