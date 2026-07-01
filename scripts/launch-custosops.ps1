$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptRoot
. (Join-Path $ScriptRoot "custosops-process-guard.ps1")

Write-Host ""
Write-Host "Launching CustosOps..."
Write-Host "Project root: $Root"
Write-Host ""

Write-Host "Stopping stale CustosOps listeners on ports 8000 and 5173..."
Stop-CustosOpsPorts -Ports @(8000, 5173)

Start-Sleep -Seconds 1

$BackendScript = Join-Path $ScriptRoot "run-backend.ps1"
$FrontendScript = Join-Path $ScriptRoot "run-frontend.ps1"

Write-Host ""
Write-Host "Starting backend window..."
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", $BackendScript
) -WorkingDirectory $Root

Write-Host "Waiting for backend health..."
$BackendOk = Wait-CustosOpsHttp -Url "http://127.0.0.1:8000/api/health" -TimeoutSeconds 45

if (-not $BackendOk) {
    Write-Host ""
    Write-Host "Backend did not become healthy within the timeout."
    Write-Host "Check the backend PowerShell window for the traceback."
    exit 1
}

Write-Host "Backend is healthy."

Write-Host ""
Write-Host "Starting frontend window..."
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", $FrontendScript
) -WorkingDirectory $Root

Write-Host "Waiting for frontend port..."
$FrontendOk = Wait-CustosOpsPort -Port 5173 -TimeoutSeconds 45

if (-not $FrontendOk) {
    Write-Host ""
    Write-Host "Frontend did not open port 5173 within the timeout."
    Write-Host "Check the frontend PowerShell window."
    exit 1
}

Write-Host "Frontend is listening."

Write-Host ""
Write-Host "Opening CustosOps..."
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "CustosOps launch completed."
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:5173"