@echo off
setlocal

rem CustosOps full proof launcher.
rem Runs the local repo audit and requires the Desktop UI proof tool.

set "REPO_ROOT=%~dp0"
if "%REPO_ROOT:~-1%"=="\" set "REPO_ROOT=%REPO_ROOT:~0,-1%"

set "PROOF_SCRIPT=%REPO_ROOT%\scripts\prove-custosops-full.ps1"

if not exist "%PROOF_SCRIPT%" (
    echo ERROR: Proof script not found:
    echo %PROOF_SCRIPT%
    echo.
    echo Make sure this file is still in the CustosOps repository root.
    pause
    exit /b 1
)

where pwsh.exe >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "POWERSHELL_EXE=pwsh.exe"
) else (
    set "POWERSHELL_EXE=powershell.exe"
)

echo CustosOps full proof
echo Repository: %REPO_ROOT%
echo PowerShell: %POWERSHELL_EXE%
echo.

pushd "%REPO_ROOT%"
%POWERSHELL_EXE% -NoProfile -ExecutionPolicy Bypass -File "%PROOF_SCRIPT%" -Root "%REPO_ROOT%" -RequireUiProof
set "PROOF_EXIT=%ERRORLEVEL%"
popd

echo.
if "%PROOF_EXIT%"=="0" (
    echo CustosOps full proof finished successfully.
) else (
    echo CustosOps full proof finished with review required. Exit code: %PROOF_EXIT%
)
echo.
pause
exit /b %PROOF_EXIT%
