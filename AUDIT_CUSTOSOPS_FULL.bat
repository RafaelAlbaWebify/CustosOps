@echo off
setlocal

rem CustosOps full local audit launcher.
rem Run this file from Explorer or any terminal. It uses the repository folder automatically.

set "REPO_ROOT=%~dp0"
set "AUDIT_SCRIPT=%REPO_ROOT%scripts\audit-custosops-local-repo.ps1"

if not exist "%AUDIT_SCRIPT%" (
    echo ERROR: Audit script not found:
    echo %AUDIT_SCRIPT%
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

echo CustosOps full local audit
echo Repository: %REPO_ROOT%
echo PowerShell: %POWERSHELL_EXE%
echo.

pushd "%REPO_ROOT%"
%POWERSHELL_EXE% -NoProfile -ExecutionPolicy Bypass -File "%AUDIT_SCRIPT%" -Root "%REPO_ROOT%" -RunExistingContractAudits -RunBackendTests -RunFrontendBuild
set "AUDIT_EXIT=%ERRORLEVEL%"
popd

echo.
if "%AUDIT_EXIT%"=="0" (
    echo CustosOps full local audit finished successfully.
) else (
    echo CustosOps full local audit finished with review required. Exit code: %AUDIT_EXIT%
)
echo.
pause
exit /b %AUDIT_EXIT%
