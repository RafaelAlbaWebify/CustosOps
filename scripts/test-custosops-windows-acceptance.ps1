[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Find-CustosOpsRoot {
    param([string]$StartingPath)

    $Candidates = New-Object System.Collections.Generic.List[string]

    if ($env:CUSTOSOPS_ROOT) {
        $Candidates.Add($env:CUSTOSOPS_ROOT)
    }

    if ($StartingPath) {
        $Current = Get-Item -LiteralPath $StartingPath -ErrorAction SilentlyContinue
        while ($Current) {
            $Candidates.Add($Current.FullName)
            $Current = $Current.Parent
        }
    }

    $CurrentLocation = (Get-Location).Path
    if ($CurrentLocation) {
        $Current = Get-Item -LiteralPath $CurrentLocation -ErrorAction SilentlyContinue
        while ($Current) {
            $Candidates.Add($Current.FullName)
            $Current = $Current.Parent
        }
    }

    $CommonRoots = @(
        (Join-Path $env:USERPROFILE "Desktop"),
        (Join-Path $env:USERPROFILE "Documents"),
        (Join-Path $env:USERPROFILE "Downloads"),
        (Join-Path $env:USERPROFILE "source"),
        (Join-Path $env:USERPROFILE "repos"),
        (Join-Path $env:USERPROFILE "GitHub")
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    foreach ($CommonRoot in $CommonRoots) {
        $Candidates.Add($CommonRoot)
        Get-ChildItem -LiteralPath $CommonRoot -Directory -Depth 4 -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -eq "CustosOps" } |
            ForEach-Object { $Candidates.Add($_.FullName) }
    }

    foreach ($Candidate in ($Candidates | Select-Object -Unique)) {
        $Launch = Join-Path $Candidate "scripts\launch-custosops.ps1"
        $Stop = Join-Path $Candidate "scripts\stop-custosops.ps1"
        $Backend = Join-Path $Candidate "backend"
        $Frontend = Join-Path $Candidate "frontend"

        if ((Test-Path -LiteralPath $Launch) -and
            (Test-Path -LiteralPath $Stop) -and
            (Test-Path -LiteralPath $Backend) -and
            (Test-Path -LiteralPath $Frontend)) {
            return (Resolve-Path -LiteralPath $Candidate).Path
        }
    }

    throw "CustosOps repository could not be located automatically."
}

function Test-HttpEndpoint {
    param(
        [Parameter(Mandatory = $true)][string]$Url,
        [int]$TimeoutSeconds = 20
    )

    try {
        $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSeconds
        return [pscustomobject]@{
            Url = $Url
            Passed = ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 400)
            StatusCode = [int]$Response.StatusCode
            Content = [string]$Response.Content
            Error = $null
        }
    }
    catch {
        return [pscustomobject]@{
            Url = $Url
            Passed = $false
            StatusCode = $null
            Content = $null
            Error = $_.Exception.Message
        }
    }
}

function Test-PortClosed {
    param([int]$Port)

    try {
        $Connection = Test-NetConnection -ComputerName "127.0.0.1" -Port $Port -WarningAction SilentlyContinue
        return (-not $Connection.TcpTestSucceeded)
    }
    catch {
        return $false
    }
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Downloads = Join-Path $env:USERPROFILE "Downloads"
$WorkRoot = Join-Path $env:TEMP "CUSTOSOPS_WINDOWS_ACCEPTANCE_$Timestamp"
$EvidenceRoot = Join-Path $WorkRoot "evidence"
$ZipPath = Join-Path $Downloads "CUSTOSOPS_WINDOWS_ACCEPTANCE_$Timestamp.zip"
$TranscriptPath = Join-Path $EvidenceRoot "acceptance-transcript.txt"
$SummaryPath = Join-Path $EvidenceRoot "acceptance-summary.json"

New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null
New-Item -ItemType Directory -Path $Downloads -Force | Out-Null

$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$Result = [ordered]@{
    timestamp = (Get-Date).ToString("o")
    computer = $env:COMPUTERNAME
    user = $env:USERNAME
    powershell = $PSVersionTable.PSVersion.ToString()
    repository_root = $null
    launch_completed = $false
    health_passed = $false
    frontend_passed = $false
    stop_completed = $false
    backend_port_closed = $false
    frontend_port_closed = $false
    overall_passed = $false
    zip_path = $ZipPath
    errors = @()
}

Start-Transcript -Path $TranscriptPath -Force | Out-Null

try {
    Write-Host "CustosOps Windows acceptance"
    Write-Host "Evidence ZIP: $ZipPath"

    $Root = Find-CustosOpsRoot -StartingPath $ScriptDirectory
    $Result.repository_root = $Root
    Write-Host "Repository: $Root"

    $LaunchScript = Join-Path $Root "scripts\launch-custosops.ps1"
    $StopScript = Join-Path $Root "scripts\stop-custosops.ps1"

    Write-Host "Launching CustosOps..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $LaunchScript
    if ($LASTEXITCODE -ne 0) {
        throw "Launch script exited with code $LASTEXITCODE."
    }
    $Result.launch_completed = $true

    Start-Sleep -Seconds 3

    $Health = Test-HttpEndpoint -Url "http://127.0.0.1:8000/api/health"
    $Frontend = Test-HttpEndpoint -Url "http://127.0.0.1:5173"

    $Health | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $EvidenceRoot "backend-health.json") -Encoding UTF8
    $Frontend | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $EvidenceRoot "frontend-response.json") -Encoding UTF8

    $Result.health_passed = [bool]$Health.Passed
    $Result.frontend_passed = [bool]$Frontend.Passed

    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.LocalPort -in @(8000, 5173) } |
        Select-Object LocalAddress, LocalPort, OwningProcess, State |
        ConvertTo-Json -Depth 4 |
        Set-Content -LiteralPath (Join-Path $EvidenceRoot "listening-ports-before-stop.json") -Encoding UTF8

    Write-Host "Stopping CustosOps..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopScript
    if ($LASTEXITCODE -ne 0) {
        throw "Stop script exited with code $LASTEXITCODE."
    }
    $Result.stop_completed = $true

    Start-Sleep -Seconds 3
    $Result.backend_port_closed = Test-PortClosed -Port 8000
    $Result.frontend_port_closed = Test-PortClosed -Port 5173

    $Result.overall_passed = (
        $Result.launch_completed -and
        $Result.health_passed -and
        $Result.frontend_passed -and
        $Result.stop_completed -and
        $Result.backend_port_closed -and
        $Result.frontend_port_closed
    )
}
catch {
    $Result.errors += $_.Exception.Message
    Write-Error $_

    try {
        if ($Result.repository_root) {
            $EmergencyStop = Join-Path $Result.repository_root "scripts\stop-custosops.ps1"
            if (Test-Path -LiteralPath $EmergencyStop) {
                & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $EmergencyStop
            }
        }
    }
    catch {
        $Result.errors += "Emergency stop failed: $($_.Exception.Message)"
    }
}
finally {
    try { Stop-Transcript | Out-Null } catch {}

    $Result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $SummaryPath -Encoding UTF8

    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }

    Compress-Archive -Path (Join-Path $EvidenceRoot "*") -DestinationPath $ZipPath -CompressionLevel Optimal -Force
    Remove-Item -LiteralPath $WorkRoot -Recurse -Force -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "Acceptance complete."
    Write-Host "Overall result: $($Result.overall_passed)"
    Write-Host "Evidence ZIP: $ZipPath"
}

if (-not $Result.overall_passed) {
    exit 1
}
