@echo off
setlocal
set "ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%scripts\test-custosops-windows-acceptance.ps1"
set "EXITCODE=%ERRORLEVEL%"
echo.
if "%EXITCODE%"=="0" (
  echo CustosOps Windows acceptance passed.
) else (
  echo CustosOps Windows acceptance reported a failure.
)
echo Evidence ZIP was written to your Downloads folder.
pause
exit /b %EXITCODE%
