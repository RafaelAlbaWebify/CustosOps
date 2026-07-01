$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptRoot
$FrontendPath = Join-Path $Root "frontend"

Set-Location -LiteralPath $FrontendPath

Write-Host ""
Write-Host "Starting CustosOps frontend..."
Write-Host "Frontend path: $FrontendPath"
Write-Host ""

if (-not (Test-Path -LiteralPath (Join-Path $FrontendPath "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    & npm.cmd install
}
else {
    Write-Host "Frontend dependencies already installed. Skipping npm install."
}

Write-Host ""
Write-Host "Frontend URL: http://localhost:5173"
Write-Host "Press CTRL+C in this window to stop the frontend."
Write-Host ""

& npm.cmd run dev -- --host 127.0.0.1