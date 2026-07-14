param()

function Get-CustosOpsProcessDetails {
    param([Parameter(Mandatory=$true)][int]$ProcessId)

    $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    $CommandLine = ""
    $ExecutablePath = ""
    $ParentProcessId = 0

    try {
        $Cim = Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessId" -ErrorAction SilentlyContinue
        if ($Cim) {
            $CommandLine = [string]$Cim.CommandLine
            $ExecutablePath = [string]$Cim.ExecutablePath
            $ParentProcessId = [int]$Cim.ParentProcessId
        }
    }
    catch {
        $CommandLine = ""
        $ExecutablePath = ""
        $ParentProcessId = 0
    }

    return [pscustomobject]@{
        PID = $ProcessId
        ParentPID = $ParentProcessId
        ProcessName = if ($Process) { $Process.ProcessName } else { "unknown" }
        CommandLine = $CommandLine
        ExecutablePath = $ExecutablePath
    }
}

function Get-CustosOpsPortProcess {
    param(
        [int[]]$Ports = @(8000, 5173)
    )

    $Items = @()

    foreach ($Port in $Ports) {
        $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

        foreach ($Connection in $Connections) {
            $Details = Get-CustosOpsProcessDetails -ProcessId $Connection.OwningProcess

            $Items += [pscustomobject]@{
                Port = $Port
                PID = $Details.PID
                ParentPID = $Details.ParentPID
                ProcessName = $Details.ProcessName
                CommandLine = $Details.CommandLine
                ExecutablePath = $Details.ExecutablePath
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

function Get-CustosOpsStopTarget {
    param(
        [Parameter(Mandatory=$true)]$Item,
        [string]$RootHint = "",
        [int]$MaximumDepth = 8
    )

    $Current = $Item
    $HighestOwned = $null
    $Visited = @{}

    for ($Depth = 0; $Depth -lt $MaximumDepth; $Depth++) {
        if (-not $Current -or $Current.PID -le 0 -or $Visited.ContainsKey([int]$Current.PID)) {
            break
        }

        $Visited[[int]$Current.PID] = $true

        if (Test-CustosOpsOwnedProcess -Item $Current -RootHint $RootHint) {
            $HighestOwned = $Current
        }
        elseif ($HighestOwned) {
            break
        }

        if (-not $Current.ParentPID -or $Current.ParentPID -le 0) {
            break
        }

        $Current = Get-CustosOpsProcessDetails -ProcessId ([int]$Current.ParentPID)
    }

    if ($HighestOwned) {
        return $HighestOwned
    }

    return $Item
}

function Wait-CustosOpsPortsClosed {
    param(
        [int[]]$Ports = @(8000, 5173),
        [int]$TimeoutSeconds = 10
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $Deadline) {
        $Remaining = @(Get-CustosOpsPortProcess -Ports $Ports)
        if ($Remaining.Count -eq 0) {
            return $true
        }

        Start-Sleep -Milliseconds 500
    }

    return (@(Get-CustosOpsPortProcess -Ports $Ports).Count -eq 0)
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
    $Targets = @{}

    foreach ($Item in $Items) {
        $Owned = Test-CustosOpsOwnedProcess -Item $Item -RootHint $RootHint

        if ($OnlyCustosOps -and (-not $Owned)) {
            Write-Host ""
            Write-Host "Port $($Item.Port) is already in use by a non-CustosOps process."
            Write-Host "PID: $($Item.PID)"
            Write-Host "Process: $($Item.ProcessName)"
            if ($Item.CommandLine) {
                Write-Host "Command line: $($Item.CommandLine)"
            }
            Write-Host "CustosOps will not force-close this process."
            Write-Host "Close that app or free the port, then launch CustosOps again."
            $SkippedForeign++
            continue
        }

        $Target = Get-CustosOpsStopTarget -Item $Item -RootHint $RootHint
        $Targets[[int]$Target.PID] = $Target
    }

    foreach ($Target in $Targets.Values) {
        Write-Host "Stopping CustosOps process tree at PID $($Target.PID) ($($Target.ProcessName))"

        try {
            $TaskKill = Start-Process -FilePath "taskkill.exe" -ArgumentList @("/PID", [string]$Target.PID, "/T", "/F") -NoNewWindow -Wait -PassThru -ErrorAction Stop
            if ($TaskKill.ExitCode -ne 0) {
                Stop-Process -Id $Target.PID -Force -ErrorAction SilentlyContinue
            }
        }
        catch {
            Stop-Process -Id $Target.PID -Force -ErrorAction SilentlyContinue
        }
    }

    $PortsClosed = Wait-CustosOpsPortsClosed -Ports $Ports -TimeoutSeconds 12

    if (-not $PortsClosed) {
        Write-Host ""
        Write-Host "One or more CustosOps ports remained open after the stop attempt."
        Show-CustosOpsProcessStatus -RootHint $RootHint
    }

    return (($SkippedForeign -eq 0) -and $PortsClosed)
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

    $Items | Select-Object Port, PID, ParentPID, ProcessName, CommandLine | Format-Table -AutoSize
}
