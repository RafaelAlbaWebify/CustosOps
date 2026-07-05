$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptRoot
. (Join-Path $ScriptRoot "custosops-process-guard.ps1")

Write-Host ""
Write-Host "Launching CustosOps..."
Write-Host "Project root: $Root"
Write-Host ""
Write-Host "First run note:"
Write-Host "- Backend dependencies may be installed into backend\.venv."
Write-Host "- Frontend dependencies may be installed into frontend\node_modules."
Write-Host "- Keep the backend and frontend PowerShell windows open while using the app."
Write-Host ""

Write-Host "Checking ports 8000 and 5173..."
$PortsOk = Stop-CustosOpsPorts -Ports @(8000, 5173) -RootHint $Root -OnlyCustosOps

if (-not $PortsOk) {
    Write-Host ""
    Write-Host "CustosOps cannot start because one or more required ports are already used by another app."
    Write-Host "See docs\onboarding\TROUBLESHOOTING.md for help."
    exit 1
}

Start-Sleep -Seconds 1

$BackendScript = Join-Path $ScriptRoot "run-backend.ps1"
$FrontendScript = Join-Path $ScriptRoot "run-frontend.ps1"

if (-not (Test-Path -LiteralPath $BackendScript)) {
    Write-Host "Missing backend launcher: $BackendScript"
    exit 1
}

if (-not (Test-Path -LiteralPath $FrontendScript)) {
    Write-Host "Missing frontend launcher: $FrontendScript"
    exit 1
}

Write-Host ""
Write-Host "Starting backend window..."
Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", $BackendScript
) -WorkingDirectory $Root

Write-Host "Waiting for backend health..."
$BackendOk = Wait-CustosOpsHttp -Url "http://127.0.0.1:8000/api/health" -TimeoutSeconds 75

if (-not $BackendOk) {
    Write-Host ""
    Write-Host "Backend did not become healthy within the timeout."
    Write-Host "Check the backend PowerShell window for the traceback."
    Write-Host "Common causes: Python missing, pip install failed, or backend import failed."
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
$FrontendOk = Wait-CustosOpsPort -Port 5173 -TimeoutSeconds 75

if (-not $FrontendOk) {
    Write-Host ""
    Write-Host "Frontend did not open port 5173 within the timeout."
    Write-Host "Check the frontend PowerShell window."
    Write-Host "Common causes: Node.js/npm missing or npm install failed."
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
Write-Host ""
Write-Host "First thing to click: Overview, then Endpoint or DNS Hygiene."