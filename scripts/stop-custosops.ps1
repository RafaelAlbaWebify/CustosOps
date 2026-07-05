$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptRoot
. (Join-Path $ScriptRoot "custosops-process-guard.ps1")

Write-Host ""
Write-Host "Stopping CustosOps local processes..."
Write-Host ""

Show-CustosOpsProcessStatus -RootHint $Root
$Stopped = Stop-CustosOpsPorts -Ports @(8000, 5173) -RootHint $Root -OnlyCustosOps

if (-not $Stopped) {
    Write-Host ""
    Write-Host "One or more required ports are used by non-CustosOps processes."
    Write-Host "CustosOps did not force-close them."
    exit 1
}

Write-Host ""
Write-Host "CustosOps stop command completed."