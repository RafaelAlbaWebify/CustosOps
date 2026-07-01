Set-StrictMode -Version Latest

Write-Host ""
Write-Host "Stopping CustosOps local processes..."
Write-Host ""

$Ports = @(8000, 5173)
$ProcessIds = New-Object System.Collections.Generic.HashSet[int]

foreach ($Port in $Ports) {
    try {
        $Connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

        foreach ($Connection in $Connections) {
            if ($Connection.OwningProcess -and $Connection.OwningProcess -gt 0) {
                [void]$ProcessIds.Add([int]$Connection.OwningProcess)
            }
        }
    }
    catch {
        Write-Host "Could not inspect port $Port"
    }
}

if ($ProcessIds.Count -eq 0) {
    Write-Host "No CustosOps processes found on ports 8000 or 5173."
    exit 0
}

foreach ($ProcessId in $ProcessIds) {
    try {
        $Process = Get-Process -Id $ProcessId -ErrorAction Stop
        Write-Host "Stopping PID $ProcessId ($($Process.ProcessName))..."
        Stop-Process -Id $ProcessId -Force
    }
    catch {
        Write-Host "Could not stop PID $ProcessId"
    }
}

Write-Host ""
Write-Host "CustosOps stop command completed."