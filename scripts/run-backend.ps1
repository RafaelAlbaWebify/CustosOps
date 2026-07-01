$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptRoot
$BackendPath = Join-Path $Root "backend"
$VenvPath = Join-Path $BackendPath ".venv"
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"

Set-Location -LiteralPath $BackendPath

Write-Host ""
Write-Host "Starting CustosOps backend..."
Write-Host "Backend path: $BackendPath"
Write-Host ""

if (-not (Test-Path -LiteralPath $PythonPath)) {
    Write-Host "Creating backend virtual environment..."
    python -m venv .venv
}

if (-not (Test-Path -LiteralPath (Join-Path $BackendPath ".deps_installed"))) {
    Write-Host "Installing backend dependencies..."
    & $PythonPath -m pip install -r requirements.txt
    New-Item -ItemType File -Path (Join-Path $BackendPath ".deps_installed") -Force | Out-Null
}
else {
    Write-Host "Backend dependencies already installed. Skipping pip install."
}

Write-Host ""
Write-Host "Checking backend import..."
& $PythonPath -c "from app.main import app; print('backend import ok')"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Backend import failed. Fix the traceback above before launching."
    exit 1
}

Write-Host ""
Write-Host "Backend URL: http://127.0.0.1:8000"
Write-Host "Press CTRL+C in this window to stop the backend."
Write-Host ""

& $PythonPath -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload