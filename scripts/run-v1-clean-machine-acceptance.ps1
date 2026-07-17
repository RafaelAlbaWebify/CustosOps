<#
CustosOps v1 Clean-Machine Acceptance Runner

Creates a fresh public clone, validates the documented launch/stop workflow,
runs the full repository audit and required Desktop UI proof, records evidence
package hashes, and writes one acceptance ZIP directly to Downloads.

This script does not modify the source checkout or open Downloads.
#>

[CmdletBinding()]
param(
    [string]$RepositoryUrl = 'https://github.com/RafaelAlbaWebify/CustosOps.git',
    [string]$Branch = 'master',
    [string]$OutputDir = '',
    [string]$UiProofScript = '',
    [int]$StartupTimeoutSeconds = 240,
    [int]$UiProofTimeoutSeconds = 900,
    [switch]$KeepFreshClone
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$StartLocation = Get-Location
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$AcceptanceOk = $true
$FailureMessages = New-Object 'System.Collections.Generic.List[string]'
$FreshRoot = Join-Path $env:TEMP ('CustosOps-v1-acceptance-' + $Stamp)
$CloneRoot = Join-Path $FreshRoot 'CustosOps'
$EvidenceRoot = Join-Path $FreshRoot 'evidence'
$SummaryPath = Join-Path $EvidenceRoot 'ACCEPTANCE_SUMMARY.txt'
$JsonPath = Join-Path $EvidenceRoot 'ACCEPTANCE_RESULT.json'
$FinalZip = $null

function Set-AcceptanceFailed {
    param([string]$Message)
    $script:AcceptanceOk = $false
    $script:FailureMessages.Add($Message)
    Write-Host $Message -ForegroundColor Red
}

function Require-Command {
    param([string]$Name)
    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $Command) {
        throw ('Required command not found: ' + $Name)
    }
    return $Command.Source
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
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-ForCondition {
    param(
        [scriptblock]$Condition,
        [int]$TimeoutSeconds,
        [string]$Description
    )

    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        if (& $Condition) { return $true }
        Start-Sleep -Milliseconds 750
    }

    Set-AcceptanceFailed ($Description + ' did not become ready within ' + $TimeoutSeconds + ' seconds.')
    return $false
}

function Invoke-NativeChecked {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$Description
    )

    Write-Host $Description -ForegroundColor Cyan
    & $FilePath @Arguments
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        throw ($Description + ' failed with exit code ' + $ExitCode)
    }
}

function Stop-FreshCustosOps {
    param([string]$RootPath)

    $StopBat = Join-Path $RootPath 'STOP_CUSTOSOPS.bat'
    if (Test-Path -LiteralPath $StopBat) {
        try {
            & cmd.exe /d /c ('"' + $StopBat + '"')
            if ($LASTEXITCODE -ne 0) {
                Set-AcceptanceFailed ('STOP_CUSTOSOPS.bat returned exit code ' + $LASTEXITCODE)
            }
        }
        catch {
            Set-AcceptanceFailed ('STOP_CUSTOSOPS.bat failed: ' + $_.Exception.Message)
        }
    }
}

try {
    if (-not $OutputDir) {
        $OutputDir = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads'
    }
    if (-not $UiProofScript) {
        $UiProofScript = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Desktop\CustosOps-UI-Tool\Run-CustosOps-UI-Smoke.ps1'
    }

    if (-not (Test-Path -LiteralPath $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }
    if (-not (Test-Path -LiteralPath $UiProofScript)) {
        throw ('Desktop UI proof tool not found: ' + $UiProofScript)
    }

    $GitExe = Require-Command -Name 'git.exe'
    [void](Require-Command -Name 'powershell.exe')
    [void](Require-Command -Name 'python.exe')
    [void](Require-Command -Name 'node.exe')
    [void](Require-Command -Name 'npm.cmd')

    New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null

    Write-Host ''
    Write-Host 'CustosOps v1 clean-machine acceptance' -ForegroundColor Cyan
    Write-Host ('Repository:  ' + $RepositoryUrl)
    Write-Host ('Branch:      ' + $Branch)
    Write-Host ('Fresh clone: ' + $CloneRoot)
    Write-Host ('Output:      ' + $OutputDir)
    Write-Host ('UI proof:    ' + $UiProofScript)
    Write-Host ''

    Invoke-NativeChecked -FilePath $GitExe -Arguments @(
        'clone', '--depth', '1', '--branch', $Branch, '--single-branch', $RepositoryUrl, $CloneRoot
    ) -Description 'Cloning a fresh public repository checkout...'

    $HeadSha = (& $GitExe -C $CloneRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $HeadSha) {
        throw 'Could not resolve fresh-clone HEAD.'
    }

    $DirtyLines = @(& $GitExe -C $CloneRoot status --porcelain)
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect fresh-clone status.' }
    if (@($DirtyLines | Where-Object { $_ -and $_.Trim() }).Count -gt 0) {
        throw 'Fresh clone is unexpectedly dirty.'
    }

    $LaunchBat = Join-Path $CloneRoot 'LAUNCH_CUSTOSOPS.bat'
    $ProofScript = Join-Path $CloneRoot 'scripts\prove-custosops-full.ps1'
    if (-not (Test-Path -LiteralPath $LaunchBat)) { throw ('Launcher not found: ' + $LaunchBat) }
    if (-not (Test-Path -LiteralPath $ProofScript)) { throw ('Proof runner not found: ' + $ProofScript) }

    $BeforeZips = @(
        Get-ChildItem -LiteralPath $OutputDir -Filter 'CUSTOSOPS_*.zip' -File -ErrorAction SilentlyContinue |
            ForEach-Object { $_.FullName }
    )

    Write-Host 'Validating documented launcher workflow...' -ForegroundColor Cyan
    & cmd.exe /d /c ('"' + $LaunchBat + '"')
    if ($LASTEXITCODE -ne 0) {
        throw ('LAUNCH_CUSTOSOPS.bat returned exit code ' + $LASTEXITCODE)
    }

    $BackendReady = Wait-ForCondition -TimeoutSeconds $StartupTimeoutSeconds -Description 'Backend health endpoint' -Condition {
        Test-HttpReady -Url 'http://127.0.0.1:8000/api/health'
    }
    $FrontendReady = Wait-ForCondition -TimeoutSeconds $StartupTimeoutSeconds -Description 'Frontend listener' -Condition {
        Test-PortReady -Port 5173
    }

    if (-not $BackendReady -or -not $FrontendReady) {
        throw 'Documented launcher acceptance failed.'
    }

    Write-Host 'Documented launcher acceptance: OK' -ForegroundColor Green
    Stop-FreshCustosOps -RootPath $CloneRoot

    Start-Sleep -Seconds 2
    if (Test-PortReady -Port 8000) { Set-AcceptanceFailed 'Port 8000 is still listening after STOP_CUSTOSOPS.bat.' }
    if (Test-PortReady -Port 5173) { Set-AcceptanceFailed 'Port 5173 is still listening after STOP_CUSTOSOPS.bat.' }
    if (-not $AcceptanceOk) { throw 'Documented stop acceptance failed.' }

    Write-Host 'Documented stop acceptance: OK' -ForegroundColor Green

    Write-Host 'Running full audit and required Desktop UI proof...' -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ProofScript `
        -Root $CloneRoot `
        -OutputDir $OutputDir `
        -UiProofScript $UiProofScript `
        -UiProofTimeoutSeconds $UiProofTimeoutSeconds `
        -AppStartupTimeoutSeconds $StartupTimeoutSeconds `
        -RequireUiProof

    $ProofExit = $LASTEXITCODE
    if ($ProofExit -ne 0) {
        throw ('Full proof runner failed with exit code ' + $ProofExit)
    }

    $NewZips = @(
        Get-ChildItem -LiteralPath $OutputDir -Filter 'CUSTOSOPS_*.zip' -File -ErrorAction SilentlyContinue |
            Where-Object { $BeforeZips -notcontains $_.FullName } |
            Sort-Object LastWriteTime
    )

    if ($NewZips.Count -eq 0) {
        throw 'No new CustosOps evidence ZIP was created in Downloads.'
    }

    $EvidenceRecords = @()
    foreach ($Zip in $NewZips) {
        $Hash = Get-FileHash -LiteralPath $Zip.FullName -Algorithm SHA256
        $EvidenceRecords += [pscustomobject]@{
            name = $Zip.Name
            path = $Zip.FullName
            size_bytes = $Zip.Length
            sha256 = $Hash.Hash.ToLowerInvariant()
            modified_utc = $Zip.LastWriteTimeUtc.ToString('o')
        }
    }

    Stop-FreshCustosOps -RootPath $CloneRoot

    $CompletedAt = Get-Date
    $SummaryLines = New-Object 'System.Collections.Generic.List[string]'
    $SummaryLines.Add('CUSTOSOPS V1 CLEAN-MACHINE ACCEPTANCE')
    $SummaryLines.Add('Generated: ' + $CompletedAt.ToString('yyyy-MM-dd HH:mm:ss zzz'))
    $SummaryLines.Add('Repository: ' + $RepositoryUrl)
    $SummaryLines.Add('Branch: ' + $Branch)
    $SummaryLines.Add('Fresh-clone HEAD: ' + $HeadSha)
    $SummaryLines.Add('Launcher acceptance: PASS')
    $SummaryLines.Add('Stop acceptance: PASS')
    $SummaryLines.Add('Full audit and required UI proof: PASS')
    $SummaryLines.Add('Downloads auto-opened: NO')
    $SummaryLines.Add('')
    $SummaryLines.Add('EVIDENCE PACKAGES')
    foreach ($Record in $EvidenceRecords) {
        $SummaryLines.Add($Record.name)
        $SummaryLines.Add('  SHA-256: ' + $Record.sha256)
        $SummaryLines.Add('  Size: ' + $Record.size_bytes + ' bytes')
    }
    $SummaryLines | Out-File -LiteralPath $SummaryPath -Encoding utf8

    [pscustomobject]@{
        schema_version = 1
        generated_at = $CompletedAt.ToString('o')
        status = 'PASS'
        repository_url = $RepositoryUrl
        branch = $Branch
        head_sha = $HeadSha
        fresh_clone_path = $CloneRoot
        launcher_acceptance = $true
        stop_acceptance = $true
        full_proof = $true
        downloads_auto_opened = $false
        evidence_packages = $EvidenceRecords
    } | ConvertTo-Json -Depth 6 | Out-File -LiteralPath $JsonPath -Encoding utf8

    $FinalZip = Join-Path $OutputDir ('CUSTOSOPS_V1_ACCEPTANCE_' + $Stamp + '.zip')
    if (Test-Path -LiteralPath $FinalZip) { Remove-Item -LiteralPath $FinalZip -Force }
    Compress-Archive -Path (Join-Path $EvidenceRoot '*') -DestinationPath $FinalZip -Force

    Write-Host ''
    Write-Host 'CUSTOSOPS V1 CLEAN-MACHINE ACCEPTANCE: PASS' -ForegroundColor Green
    Write-Host ('Fresh-clone HEAD: ' + $HeadSha)
    Write-Host ('Acceptance ZIP: ' + $FinalZip)
    foreach ($Record in $EvidenceRecords) {
        Write-Host ($Record.name + '  SHA-256 ' + $Record.sha256)
    }
}
catch {
    Set-AcceptanceFailed $_.Exception.Message

    if (-not (Test-Path -LiteralPath $EvidenceRoot)) {
        New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null
    }

    @(
        'CUSTOSOPS V1 CLEAN-MACHINE ACCEPTANCE',
        'Generated: ' + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'),
        'Status: FAIL',
        'Repository: ' + $RepositoryUrl,
        'Branch: ' + $Branch,
        '',
        'FAILURES',
        ($FailureMessages -join [Environment]::NewLine)
    ) | Out-File -LiteralPath $SummaryPath -Encoding utf8

    if ($OutputDir -and (Test-Path -LiteralPath $OutputDir)) {
        $FinalZip = Join-Path $OutputDir ('CUSTOSOPS_V1_ACCEPTANCE_FAILED_' + $Stamp + '.zip')
        Compress-Archive -Path (Join-Path $EvidenceRoot '*') -DestinationPath $FinalZip -Force
        Write-Host ('Failure evidence ZIP: ' + $FinalZip) -ForegroundColor Yellow
    }
}
finally {
    try {
        if (Test-Path -LiteralPath $CloneRoot) {
            Stop-FreshCustosOps -RootPath $CloneRoot
        }
    }
    catch {}

    Set-Location $StartLocation

    if (-not $KeepFreshClone -and (Test-Path -LiteralPath $FreshRoot)) {
        try { Remove-Item -LiteralPath $FreshRoot -Recurse -Force } catch {}
    }
}

if ($AcceptanceOk) { exit 0 }
exit 1
