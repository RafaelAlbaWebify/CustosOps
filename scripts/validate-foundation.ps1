Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot

Write-Host "Validating backend..."
Set-Location -LiteralPath (Join-Path $Root 'backend')

if (-not (Test-Path -LiteralPath '.venv')) {
    python -m venv .venv
}

.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pytest

Write-Host "Validating frontend..."
Set-Location -LiteralPath (Join-Path $Root 'frontend')
npm install
npm run build

Write-Host "CustosOps foundation validation completed."