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

            try {
                $Cim = Get-CimInstance Win32_Process -Filter "ProcessId=$($Connection.OwningProcess)" -ErrorAction SilentlyContinue
                if ($Cim) {
                    $CommandLine = $Cim.CommandLine
                }
            }
            catch {
                $CommandLine = ""
            }

            $Items += [pscustomobject]@{
                Port = $Port
                PID = $Connection.OwningProcess
                ProcessName = if ($Process) { $Process.ProcessName } else { "unknown" }
                CommandLine = $CommandLine
            }
        }
    }

    return $Items
}

function Stop-CustosOpsPorts {
    param(
        [int[]]$Ports = @(8000, 5173)
    )

    $Items = @(Get-CustosOpsPortProcess -Ports $Ports)

    if ($Items.Count -eq 0) {
        Write-Host "No CustosOps listener processes found on ports: $($Ports -join ', ')"
        return
    }

    $Groups = $Items | Group-Object PID

    foreach ($Group in $Groups) {
        $PidValue = [int]$Group.Name
        $PortsText = (($Group.Group | Select-Object -ExpandProperty Port) -join ", ")
        $Name = ($Group.Group | Select-Object -First 1).ProcessName

        Write-Host "Stopping PID $PidValue ($Name) listening on port(s): $PortsText"

        try {
            Stop-Process -Id $PidValue -Force -ErrorAction Stop
        }
        catch {
            Write-Host "Could not stop PID $PidValue. It may have already exited."
        }
    }

    Start-Sleep -Seconds 1
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
    $Items = @(Get-CustosOpsPortProcess)

    if ($Items.Count -eq 0) {
        Write-Host "CustosOps ports are free."
        return
    }

    $Items | Format-Table Port, PID, ProcessName, CommandLine -AutoSize
}