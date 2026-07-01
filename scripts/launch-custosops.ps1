Set-StrictMode -Version Latest

$Root = Split-Path -Parent $PSScriptRoot

$BackendScript = Join-Path $Root 'scripts\run-backend.ps1'
$FrontendScript = Join-Path $Root 'scripts\run-frontend.ps1'

Write-Host ""
Write-Host "Launching CustosOps..."
Write-Host "Project root: $Root"
Write-Host ""

if (-not (Test-Path -LiteralPath $BackendScript)) {
    Write-Host "Missing backend script: $BackendScript"
    exit 1
}

if (-not (Test-Path -LiteralPath $FrontendScript)) {
    Write-Host "Missing frontend script: $FrontendScript"
    exit 1
}

Start-Process powershell.exe -ArgumentList @(
    '-NoExit',
    '-ExecutionPolicy', 'Bypass',
    '-File', $BackendScript
) -WorkingDirectory $Root

Start-Sleep -Seconds 3

Start-Process powershell.exe -ArgumentList @(
    '-NoExit',
    '-ExecutionPolicy', 'Bypass',
    '-File', $FrontendScript
) -WorkingDirectory $Root

Write-Host "Waiting for the frontend to start..."
Start-Sleep -Seconds 8

Start-Process 'http://localhost:5173'

Write-Host ""
Write-Host "CustosOps launch sequence started."
Write-Host "Backend:  http://127.0.0.1:8000"
Write-Host "Frontend: http://localhost:5173"
Write-Host ""
Write-Host "You can close this launcher window."