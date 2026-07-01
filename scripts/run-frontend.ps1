Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot
$FrontendRoot = Join-Path $Root 'frontend'

Set-Location -LiteralPath $FrontendRoot

Write-Host ""
Write-Host "Starting CustosOps frontend..."
Write-Host "Frontend path: $FrontendRoot"
Write-Host ""

if (-not (Test-Path -LiteralPath 'node_modules')) {
    Write-Host "Installing frontend dependencies..."
    & npm.cmd install

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Frontend dependency installation failed."
        exit 1
    }
}
else {
    Write-Host "Frontend dependencies already installed. Skipping npm install."
}

Write-Host ""
Write-Host "Frontend URL: http://localhost:5173"
Write-Host "Press CTRL+C in this window to stop the frontend."
Write-Host ""

& npm.cmd run dev