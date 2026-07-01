$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
. (Join-Path $ScriptRoot "custosops-process-guard.ps1")

Write-Host ""
Write-Host "Stopping CustosOps local processes..."
Write-Host ""

Show-CustosOpsProcessStatus
Stop-CustosOpsPorts -Ports @(8000, 5173)

Write-Host ""
Write-Host "CustosOps stop command completed."