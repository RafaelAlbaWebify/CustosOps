param()

function Get-CustosOpsPortProcess {
    param(
        [int[]]$Ports = @(8000, 5173)
    )

    $Items = @()

    foreach ($Port in $Ports) {
        $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

        foreach ($Connection in $Connections) {
            $Process = Get-Process -Id $Connection.OwningProcess -ErrorAction SilentlyContinue
            $CommandLine = ""
            $ExecutablePath = ""

            try {
                $Cim = Get-CimInstance Win32_Process -Filter "ProcessId=$($Connection.OwningProcess)" -ErrorAction SilentlyContinue
                if ($Cim) {
                    $CommandLine = [string]$Cim.CommandLine
                    $ExecutablePath = [string]$Cim.ExecutablePath
                }
            }
            catch {
                $CommandLine = ""
                $ExecutablePath = ""
            }

            $Items += [pscustomobject]@{
                Port = $Port
                PID = $Connection.OwningProcess
                ProcessName = if ($Process) { $Process.ProcessName } else { "unknown" }
                CommandLine = $CommandLine
                ExecutablePath = $ExecutablePath
            }
        }
    }

    return $Items
}

function Test-CustosOpsOwnedProcess {
    param(
        [Parameter(Mandatory=$true)]$Item,
        [string]$RootHint = ""
    )

    $CommandLine = ([string]$Item.CommandLine)
    $ExecutablePath = ([string]$Item.ExecutablePath)
    $Combined = ($CommandLine + " " + $ExecutablePath).ToLowerInvariant()

    if ($RootHint) {
        $RootLower = $RootHint.TrimEnd('\').ToLowerInvariant()
        if ($RootLower -and $Combined.Contains($RootLower)) {
            return $true
        }
    }

    if ($Combined -match 'custosops') {
        return $true
    }

    if ($Combined -match 'uvicorn\s+app\.main:app') {
        return $true
    }

    if ($Combined -match 'node_modules[\\\/]vite') {
        return $true
    }

    if ($Combined -match 'run-backend\.ps1') {
        return $true
    }

    if ($Combined -match 'run-frontend\.ps1') {
        return $true
    }

    return $false
}

function Stop-CustosOpsPorts {
    param(
        [int[]]$Ports = @(8000, 5173),
        [string]$RootHint = "",
        [switch]$OnlyCustosOps
    )

    $Items = @(Get-CustosOpsPortProcess -Ports $Ports)

    if ($Items.Count -eq 0) {
        Write-Host "No listener processes found on ports: $($Ports -join ', ')"
        return $true
    }

    $SkippedForeign = 0
    $Groups = $Items | Group-Object PID

    foreach ($Group in $Groups) {
        $PidValue = [int]$Group.Name
        $PortsText = (($Group.Group | Select-Object -ExpandProperty Port) -join ", ")
        $Name = ($Group.Group | Select-Object -First 1).ProcessName
        $CommandLine = ($Group.Group | Select-Object -First 1).CommandLine

        $Owned = $false
        foreach ($Item in $Group.Group) {
            if (Test-CustosOpsOwnedProcess -Item $Item -RootHint $RootHint) {
                $Owned = $true
            }
        }

        if ($OnlyCustosOps -and (-not $Owned)) {
            Write-Host ""
            Write-Host "Port(s) $PortsText are already in use by a non-CustosOps process."
            Write-Host "PID: $PidValue"
            Write-Host "Process: $Name"
            if ($CommandLine) {
                Write-Host "Command line: $CommandLine"
            }
            Write-Host "CustosOps will not force-close this process."
            Write-Host "Close that app or free the port, then launch CustosOps again."
            $SkippedForeign++
            continue
        }

        Write-Host "Stopping PID $PidValue ($Name) listening on port(s): $PortsText"

        try {
            Stop-Process -Id $PidValue -Force -ErrorAction Stop
        }
        catch {
            Write-Host "Could not stop PID $PidValue. It may have already exited."
        }
    }

    Start-Sleep -Seconds 1
    return ($SkippedForeign -eq 0)
}

function Wait-CustosOpsPort {
    param(
        [Parameter(Mandatory=$true)][int]$Port,
        [int]$TimeoutSeconds = 30
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $Deadline) {
        $Connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

        if ($Connection) {
            return $true
        }

        Start-Sleep -Milliseconds 500
    }

    return $false
}

function Wait-CustosOpsHttp {
    param(
        [Parameter(Mandatory=$true)][string]$Url,
        [int]$TimeoutSeconds = 30
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $Deadline) {
        try {
            $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop

            if ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500) {
                return $true
            }
        }
        catch {
            Start-Sleep -Milliseconds 700
        }
    }

    return $false
}

function Show-CustosOpsProcessStatus {
    param(
        [string]$RootHint = ""
    )

    $Items = @(Get-CustosOpsPortProcess)

    if ($Items.Count -eq 0) {
        Write-Host "CustosOps ports are free."
        return
    }

    $Items | Select-Object Port, PID, ProcessName, CommandLine | Format-Table -AutoSize
}