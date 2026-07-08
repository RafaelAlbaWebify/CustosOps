<#
CustosOps Full Proof Runner

Runs the repository audit and, when required, the external Desktop UI proof tool.
This script does not modify source files.
#>

param(
    [string]$Root = '.',
    [string]$OutputDir = '',
    [string]$UiProofScript = '',
    [int]$UiProofTimeoutSeconds = 600,
    [int]$AppStartupTimeoutSeconds = 180,
    [switch]$SkipUiProof,
    [switch]$RequireUiProof
)

$ErrorActionPreference = 'Continue'
$ProofOk = $true

function Resolve-ProofRoot {
    param([string]$Path)
    try {
        return (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
    }
    catch {
        Write-Host 'ERROR: Root path not found.' -ForegroundColor Red
        exit 1
    }
}

function Set-Failed {
    param([string]$Message)
    $script:ProofOk = $false
    Write-Host $Message -ForegroundColor Red
}

function Get-ChildPowerShellExe {
    $Pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
    if ($Pwsh) { return $Pwsh.Source }

    $WindowsPowerShell = Get-Command powershell.exe -ErrorAction SilentlyContinue
    if ($WindowsPowerShell) { return $WindowsPowerShell.Source }

    return 'powershell.exe'
}

function Invoke-UiProofWithTimeout {
    param(
        [string]$ScriptPath,
        [int]$TimeoutSeconds
    )

    $Psi = New-Object System.Diagnostics.ProcessStartInfo
    $Psi.FileName = 'powershell.exe'
    [void]$Psi.ArgumentList.Add('-NoProfile')
    [void]$Psi.ArgumentList.Add('-ExecutionPolicy')
    [void]$Psi.ArgumentList.Add('Bypass')
    [void]$Psi.ArgumentList.Add('-File')
    [void]$Psi.ArgumentList.Add($ScriptPath)
    $Psi.UseShellExecute = $false

    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $Psi
    [void]$Process.Start()

    if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
        try { $Process.Kill($true) } catch { try { $Process.Kill() } catch {} }
        Write-Host ('Desktop UI proof timed out after ' + $TimeoutSeconds + ' seconds.') -ForegroundColor Red
        return 124
    }

    return $Process.ExitCode
}

function Test-HttpReady {
    param([string]$Url)

    try {
        $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        return ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500)
    }
    catch {
        return $false
    }
}

function Test-PortReady {
    param([int]$Port)

    $Connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return [bool]$Connection
}

function Start-CustosOpsProofProcess {
    param(
        [string]$ScriptPath,
        [string]$WorkingDirectory,
        [string]$Name
    )

    Write-Host ('Starting ' + $Name + ' for proof...') -ForegroundColor Cyan
    Start-Process powershell.exe -ArgumentList @(
        '-NoExit',
        '-ExecutionPolicy', 'Bypass',
        '-File', $ScriptPath
    ) -WorkingDirectory $WorkingDirectory | Out-Null
}

function Wait-ForBackendReady {
    param([int]$TimeoutSeconds)

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        if (Test-HttpReady -Url 'http://127.0.0.1:8000/api/health') {
            return $true
        }
        Start-Sleep -Milliseconds 700
    }

    return $false
}

function Wait-ForFrontendReady {
    param([int]$TimeoutSeconds)

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        if (Test-PortReady -Port 5173) {
            return $true
        }
        Start-Sleep -Milliseconds 700
    }

    return $false
}

function Ensure-CustosOpsReadyForProof {
    param(
        [string]$RootPath,
        [int]$TimeoutSeconds
    )

    $BackendScript = Join-Path $RootPath 'scripts\run-backend.ps1'
    $FrontendScript = Join-Path $RootPath 'scripts\run-frontend.ps1'
    $GuardScript = Join-Path $RootPath 'scripts\custosops-process-guard.ps1'

    if (-not (Test-Path -LiteralPath $BackendScript)) {
        Set-Failed ('Backend launcher not found: ' + $BackendScript)
        return $false
    }

    if (-not (Test-Path -LiteralPath $FrontendScript)) {
        Set-Failed ('Frontend launcher not found: ' + $FrontendScript)
        return $false
    }

    $BackendReady = Test-HttpReady -Url 'http://127.0.0.1:8000/api/health'
    $FrontendReady = Test-PortReady -Port 5173

    if ($BackendReady) {
        Write-Host 'Backend proof preflight: already ready' -ForegroundColor Green
    }

    if ($FrontendReady) {
        Write-Host 'Frontend proof preflight: already listening' -ForegroundColor Green
    }

    $PortsToClear = @()
    if (-not $BackendReady) { $PortsToClear += 8000 }
    if (-not $FrontendReady) { $PortsToClear += 5173 }

    if ($PortsToClear.Count -gt 0 -and (Test-Path -LiteralPath $GuardScript)) {
        . $GuardScript
        $PortsOk = Stop-CustosOpsPorts -Ports $PortsToClear -RootHint $RootPath -OnlyCustosOps

        if (-not $PortsOk) {
            $BackendReady = Test-HttpReady -Url 'http://127.0.0.1:8000/api/health'
            $FrontendReady = Test-PortReady -Port 5173

            if (($PortsToClear -contains 8000) -and (-not $BackendReady)) {
                Set-Failed 'Port 8000 is occupied and no healthy CustosOps backend answered /api/health.'
                return $false
            }

            if (($PortsToClear -contains 5173) -and (-not $FrontendReady)) {
                Set-Failed 'Port 5173 is occupied and no frontend listener is available.'
                return $false
            }
        }
    }

    if (-not (Test-HttpReady -Url 'http://127.0.0.1:8000/api/health')) {
        Start-CustosOpsProofProcess -ScriptPath $BackendScript -WorkingDirectory $RootPath -Name 'backend'

        if (-not (Wait-ForBackendReady -TimeoutSeconds ([Math]::Min($TimeoutSeconds, 120)))) {
            Set-Failed 'Backend did not become ready before UI proof.'
            return $false
        }
    }

    Write-Host 'Backend proof preflight: OK' -ForegroundColor Green

    if (-not (Test-PortReady -Port 5173)) {
        Start-CustosOpsProofProcess -ScriptPath $FrontendScript -WorkingDirectory $RootPath -Name 'frontend'

        if (-not (Wait-ForFrontendReady -TimeoutSeconds $TimeoutSeconds)) {
            Set-Failed 'Frontend did not open port 5173 before UI proof.'
            return $false
        }
    }

    Write-Host 'Frontend proof preflight: OK' -ForegroundColor Green
    return $true
}

$RootPath = Resolve-ProofRoot -Path $Root
if (-not $OutputDir) {
    if ($env:USERPROFILE) { $OutputDir = Join-Path $env:USERPROFILE 'Downloads' }
    else { $OutputDir = [Environment]::GetFolderPath('UserProfile') }
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$AuditScript = Join-Path $RootPath 'scripts\audit-custosops-local-repo.ps1'
$ProofChecker = Join-Path $RootPath 'scripts\check-ui-proof-artifact.ps1'
$ChildPowerShell = Get-ChildPowerShellExe

Write-Host ''
Write-Host 'CustosOps full proof runner' -ForegroundColor Cyan
Write-Host ('Repository: ' + $RootPath)
Write-Host ('OutputDir:  ' + $OutputDir)
Write-Host ('PowerShell: ' + $ChildPowerShell)
Write-Host ('App startup timeout: ' + $AppStartupTimeoutSeconds + ' seconds')
Write-Host ('UI timeout: ' + $UiProofTimeoutSeconds + ' seconds')
Write-Host ''

if (-not (Test-Path -LiteralPath $AuditScript)) {
    Set-Failed ('ERROR: Local audit script not found: ' + $AuditScript)
}
else {
    Write-Host 'Step 1/2: Running full local repository audit...' -ForegroundColor Cyan
    & $ChildPowerShell -NoProfile -ExecutionPolicy Bypass -File $AuditScript -Root $RootPath -OutputDir $OutputDir -RunExistingContractAudits -RunBackendTests -RunFrontendBuild
    $AuditExit = $LASTEXITCODE
    if ($AuditExit -ne 0) {
        Set-Failed ('Local repository audit failed with exit code ' + $AuditExit)
    }
    else {
        Write-Host 'Local repository audit: OK' -ForegroundColor Green
    }
}

if ($SkipUiProof) {
    Write-Host 'Step 2/2: Desktop UI proof skipped by request.' -ForegroundColor Yellow
}
else {
    if (-not $UiProofScript) {
        if ($env:USERPROFILE) {
            $UiProofScript = Join-Path $env:USERPROFILE 'Desktop\CustosOps-UI-Tool\Run-CustosOps-UI-Smoke.ps1'
        }
    }

    if (-not $UiProofScript -or -not (Test-Path -LiteralPath $UiProofScript)) {
        $Message = 'Desktop UI proof tool not found. Expected: ' + $UiProofScript
        if ($RequireUiProof) { Set-Failed $Message }
        else { Write-Host $Message -ForegroundColor Yellow }
    }
    elseif (-not (Test-Path -LiteralPath $ProofChecker)) {
        Set-Failed ('ERROR: UI proof checker not found: ' + $ProofChecker)
    }
    elseif ($ProofOk) {
        Write-Host 'Step 2/2: Preparing app for Desktop UI proof...' -ForegroundColor Cyan
        $AppReady = Ensure-CustosOpsReadyForProof -RootPath $RootPath -TimeoutSeconds $AppStartupTimeoutSeconds

        if ($AppReady) {
            Write-Host 'Step 2/2: Running Desktop UI proof...' -ForegroundColor Cyan
            $BeforeProofZips = @(Get-ChildItem -LiteralPath $OutputDir -Filter 'CUSTOSOPS_UI_SMOKE_*.zip' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })

            $UiProofExit = Invoke-UiProofWithTimeout -ScriptPath $UiProofScript -TimeoutSeconds $UiProofTimeoutSeconds
            if ($UiProofExit -ne 0) {
                Set-Failed ('Desktop UI proof failed with exit code ' + $UiProofExit)
            }

            $LatestProofZip = Get-ChildItem -LiteralPath $OutputDir -Filter 'CUSTOSOPS_UI_SMOKE_*.zip' -File -ErrorAction SilentlyContinue |
                Where-Object { $BeforeProofZips -notcontains $_.FullName } |
                Sort-Object LastWriteTime -Descending |
                Select-Object -First 1

            if (-not $LatestProofZip) {
                $LatestProofZip = Get-ChildItem -LiteralPath $OutputDir -Filter 'CUSTOSOPS_UI_SMOKE_*.zip' -File -ErrorAction SilentlyContinue |
                    Sort-Object LastWriteTime -Descending |
                    Select-Object -First 1
            }

            if (-not $LatestProofZip) {
                Set-Failed 'Desktop UI proof ZIP not found in output directory.'
            }
            else {
                $ProofStatusFile = Join-Path $OutputDir ('CUSTOSOPS_UI_PROOF_CHECK_STATUS_' + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.txt')
                Write-Host ('Desktop UI proof ZIP: ' + $LatestProofZip.FullName)
                & $ChildPowerShell -NoProfile -ExecutionPolicy Bypass -File $ProofChecker -ZipPath $LatestProofZip.FullName -StatusFile $ProofStatusFile
                $ProofCheckExit = $LASTEXITCODE
                $ProofCheckStatus = ''
                if (Test-Path -LiteralPath $ProofStatusFile) {
                    $ProofCheckStatus = (Get-Content -LiteralPath $ProofStatusFile -Raw).Trim()
                }

                if ($ProofCheckExit -ne 0 -or $ProofCheckStatus -ne 'OK') {
                    Set-Failed ('Desktop UI proof artifact check failed. Exit code: ' + $ProofCheckExit + '. Status: ' + $ProofCheckStatus)
                }
                else {
                    Write-Host 'Desktop UI proof artifact check: OK' -ForegroundColor Green
                }
            }
        }
    }
}

Write-Host ''
if ($ProofOk) {
    Write-Host 'CustosOps full proof runner finished successfully.' -ForegroundColor Green
    exit 0
}

Write-Host 'CustosOps full proof runner finished with review required.' -ForegroundColor Red
exit 1
