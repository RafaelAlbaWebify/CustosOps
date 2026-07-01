Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$BackendRoot = Join-Path $Root 'backend'

Set-Location -LiteralPath $BackendRoot

Write-Host ""
Write-Host "Starting CustosOps backend..."
Write-Host "Backend path: $BackendRoot"
Write-Host ""

if (-not (Test-Path -LiteralPath '.venv')) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}

$Python = Join-Path $BackendRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    Write-Host "Python virtual environment was not created correctly."
    exit 1
}

if (-not (Test-Path -LiteralPath '.deps_installed')) {
    Write-Host "Installing backend dependencies..."
    & $Python -m pip install -r requirements.txt

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Backend dependency installation failed."
        exit 1
    }

    Get-Date -Format 'yyyy-MM-dd HH:mm:ss' | Set-Content -LiteralPath '.deps_installed' -Encoding UTF8
}
else {
    Write-Host "Backend dependencies already installed. Skipping pip install."
}

Write-Host ""
Write-Host "Backend URL: http://127.0.0.1:8000"
Write-Host "Press CTRL+C in this window to stop the backend."
Write-Host ""

& $Python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload