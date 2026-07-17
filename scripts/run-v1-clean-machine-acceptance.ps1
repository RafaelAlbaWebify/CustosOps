<#
CustosOps v1 Clean-Machine Acceptance Runner

Creates a fresh public clone, validates launch and stop behavior, runs the full
repository audit, executes the repository-owned Playwright workspace/SOC suite,
records evidence hashes, and writes one acceptance ZIP directly to Downloads.
#>

[CmdletBinding()]
param(
    [string]$RepositoryUrl = 'https://github.com/RafaelAlbaWebify/CustosOps.git',
    [string]$Branch = 'master',
    [string]$OutputDir = '',
    [int]$StartupTimeoutSeconds = 240,
    [int]$PlaywrightTimeoutSeconds = 900,
    [switch]$KeepFreshClone
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

$StartLocation = Get-Location
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$FreshRoot = Join-Path $env:TEMP ('CustosOps-v1-acceptance-' + $Stamp)
$CloneRoot = Join-Path $FreshRoot 'CustosOps'
$EvidenceRoot = Join-Path $FreshRoot 'evidence'
$SummaryPath = Join-Path $EvidenceRoot 'ACCEPTANCE_SUMMARY.txt'
$JsonPath = Join-Path $EvidenceRoot 'ACCEPTANCE_RESULT.json'
$FinalZip = $null
$HeadSha = ''
$FailureMessage = ''

function Require-Command {
    param([Parameter(Mandatory = $true)][string]$Name)
    $Command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $Command) { throw ('Required command not found: ' + $Name) }
    return $Command.Source
}

function Test-HttpReady {
    param([Parameter(Mandatory = $true)][string]$Url)
    try {
        $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
        return ($Response.StatusCode -ge 200 -and $Response.StatusCode -lt 500)
    }
    catch { return $false }
}

function Test-PortReady {
    param([Parameter(Mandatory = $true)][int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

function Wait-ForCondition {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Condition,
        [Parameter(Mandatory = $true)][int]$TimeoutSeconds,
        [Parameter(Mandatory = $true)][string]$Description
    )
    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        if (& $Condition) { return }
        Start-Sleep -Milliseconds 750
    }
    throw ($Description + ' did not become ready within ' + $TimeoutSeconds + ' seconds.')
}

function Invoke-NativeChecked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$Description
    )
    Write-Host $Description -ForegroundColor Cyan
    & $FilePath @Arguments
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) { throw ($Description + ' failed with exit code ' + $ExitCode) }
}

function Stop-FreshCustosOps {
    param([Parameter(Mandatory = $true)][string]$RootPath)
    $StopBat = Join-Path $RootPath 'STOP_CUSTOSOPS.bat'
    if (-not (Test-Path -LiteralPath $StopBat)) { return }
    & cmd.exe /d /c ('"' + $StopBat + '"')
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) { throw ('STOP_CUSTOSOPS.bat returned exit code ' + $ExitCode) }
}

function Copy-DirectoryIfPresent {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )
    if (Test-Path -LiteralPath $Source) {
        Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
    }
}

try {
    if (-not $OutputDir) {
        $OutputDir = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads'
    }
    if (-not (Test-Path -LiteralPath $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }

    $GitExe = Require-Command -Name 'git.exe'
    [void](Require-Command -Name 'powershell.exe')
    [void](Require-Command -Name 'python.exe')
    [void](Require-Command -Name 'node.exe')
    [void](Require-Command -Name 'npm.cmd')
    [void](Require-Command -Name 'npx.cmd')

    New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null

    Write-Host ''
    Write-Host 'CustosOps v1 clean-machine acceptance' -ForegroundColor Cyan
    Write-Host ('Repository:  ' + $RepositoryUrl)
    Write-Host ('Branch:      ' + $Branch)
    Write-Host ('Fresh clone: ' + $CloneRoot)
    Write-Host ('Output:      ' + $OutputDir)
    Write-Host 'UI proof:    repository-owned Playwright suite'
    Write-Host ''

    Invoke-NativeChecked -FilePath $GitExe -Arguments @(
        'clone', '--depth', '1', '--branch', $Branch, '--single-branch', $RepositoryUrl, $CloneRoot
    ) -Description 'Cloning a fresh public repository checkout...'

    $HeadSha = (& $GitExe -C $CloneRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or -not $HeadSha) { throw 'Could not resolve fresh-clone HEAD.' }

    $DirtyLines = @(& $GitExe -C $CloneRoot status --porcelain)
    if ($LASTEXITCODE -ne 0) { throw 'Could not inspect fresh-clone status.' }
    if (@($DirtyLines | Where-Object { $_ -and $_.Trim() }).Count -gt 0) {
        throw 'Fresh clone is unexpectedly dirty.'
    }

    $LaunchBat = Join-Path $CloneRoot 'LAUNCH_CUSTOSOPS.bat'
    $AuditScript = Join-Path $CloneRoot 'scripts\audit-custosops-local-repo.ps1'
    $FrontendRoot = Join-Path $CloneRoot 'frontend'
    if (-not (Test-Path -LiteralPath $LaunchBat)) { throw ('Launcher not found: ' + $LaunchBat) }
    if (-not (Test-Path -LiteralPath $AuditScript)) { throw ('Audit runner not found: ' + $AuditScript) }

    $BeforeZips = @(
        Get-ChildItem -LiteralPath $OutputDir -Filter 'CUSTOSOPS_*.zip' -File -ErrorAction SilentlyContinue |
            ForEach-Object { $_.FullName }
    )

    Write-Host 'Validating documented launcher workflow...' -ForegroundColor Cyan
    & cmd.exe /d /c ('"' + $LaunchBat + '"')
    if ($LASTEXITCODE -ne 0) { throw ('LAUNCH_CUSTOSOPS.bat returned exit code ' + $LASTEXITCODE) }

    Wait-ForCondition -TimeoutSeconds $StartupTimeoutSeconds -Description 'Backend health endpoint' -Condition {
        Test-HttpReady -Url 'http://127.0.0.1:8000/api/health'
    }
    Wait-ForCondition -TimeoutSeconds $StartupTimeoutSeconds -Description 'Frontend listener' -Condition {
        Test-PortReady -Port 5173
    }

    Write-Host 'Documented launcher acceptance: OK' -ForegroundColor Green
    Stop-FreshCustosOps -RootPath $CloneRoot
    Start-Sleep -Seconds 2
    if (Test-PortReady -Port 8000) { throw 'Port 8000 is still listening after STOP_CUSTOSOPS.bat.' }
    if (Test-PortReady -Port 5173) { throw 'Port 5173 is still listening after STOP_CUSTOSOPS.bat.' }
    Write-Host 'Documented stop acceptance: OK' -ForegroundColor Green

    Write-Host 'Running full local repository audit...' -ForegroundColor Cyan
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $AuditScript `
        -Root $CloneRoot `
        -OutputDir $OutputDir `
        -RunExistingContractAudits `
        -RunBackendTests `
        -RunFrontendBuild
    if ($LASTEXITCODE -ne 0) { throw ('Full local repository audit failed with exit code ' + $LASTEXITCODE) }
    Write-Host 'Full local repository audit: OK' -ForegroundColor Green

    Write-Host 'Preparing application for local Playwright proof...' -ForegroundColor Cyan
    & cmd.exe /d /c ('"' + $LaunchBat + '"')
    if ($LASTEXITCODE -ne 0) { throw ('LAUNCH_CUSTOSOPS.bat returned exit code ' + $LASTEXITCODE + ' before Playwright proof') }

    Wait-ForCondition -TimeoutSeconds $StartupTimeoutSeconds -Description 'Backend health endpoint for Playwright' -Condition {
        Test-HttpReady -Url 'http://127.0.0.1:8000/api/health'
    }
    Wait-ForCondition -TimeoutSeconds $StartupTimeoutSeconds -Description 'Frontend listener for Playwright' -Condition {
        Test-PortReady -Port 5173
    }

    Push-Location $FrontendRoot
    try {
        Invoke-NativeChecked -FilePath 'npx.cmd' -Arguments @('playwright', 'install', 'chromium') -Description 'Installing Playwright Chromium...'

        $StdOutPath = Join-Path $EvidenceRoot 'playwright-stdout.log'
        $StdErrPath = Join-Path $EvidenceRoot 'playwright-stderr.log'
        $PreviousBaseUrl = $env:CUSTOSOPS_BASE_URL
        $env:CUSTOSOPS_BASE_URL = 'http://127.0.0.1:5173'

        try {
            Write-Host 'Running repository-owned Playwright workspace and SOC proof...' -ForegroundColor Cyan
            $Process = Start-Process -FilePath 'cmd.exe' `
                -ArgumentList @('/d', '/c', 'npm.cmd run test:e2e') `
                -WorkingDirectory $FrontendRoot `
                -RedirectStandardOutput $StdOutPath `
                -RedirectStandardError $StdErrPath `
                -PassThru

            if (-not $Process.WaitForExit($PlaywrightTimeoutSeconds * 1000)) {
                try { $Process.Kill() } catch {}
                throw ('Playwright proof timed out after ' + $PlaywrightTimeoutSeconds + ' seconds.')
            }

            $Process.WaitForExit()
            $Process.Refresh()
            $PlaywrightExitCode = [int]$Process.ExitCode
            if ($PlaywrightExitCode -ne 0) {
                throw ('Playwright proof failed with exit code ' + $PlaywrightExitCode)
            }
        }
        finally {
            $env:CUSTOSOPS_BASE_URL = $PreviousBaseUrl
        }
    }
    finally {
        Pop-Location
    }

    Copy-DirectoryIfPresent -Source (Join-Path $FrontendRoot 'playwright-report') -Destination (Join-Path $EvidenceRoot 'playwright-report')
    Copy-DirectoryIfPresent -Source (Join-Path $FrontendRoot 'test-results') -Destination (Join-Path $EvidenceRoot 'test-results')

    Write-Host 'Repository-owned Playwright proof: OK' -ForegroundColor Green
    Stop-FreshCustosOps -RootPath $CloneRoot

    $NewZips = @(
        Get-ChildItem -LiteralPath $OutputDir -Filter 'CUSTOSOPS_*.zip' -File -ErrorAction SilentlyContinue |
            Where-Object { $BeforeZips -notcontains $_.FullName } |
            Sort-Object LastWriteTime
    )
    if ($NewZips.Count -eq 0) { throw 'No new CustosOps audit ZIP was created in Downloads.' }

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

    $CompletedAt = Get-Date
    $SummaryLines = New-Object 'System.Collections.Generic.List[string]'
    $SummaryLines.Add('CUSTOSOPS V1 CLEAN-MACHINE ACCEPTANCE')
    $SummaryLines.Add(('Generated: ' + $CompletedAt.ToString('yyyy-MM-dd HH:mm:ss zzz')))
    $SummaryLines.Add(('Repository: ' + $RepositoryUrl))
    $SummaryLines.Add(('Branch: ' + $Branch))
    $SummaryLines.Add(('Fresh-clone HEAD: ' + $HeadSha))
    $SummaryLines.Add('Launcher acceptance: PASS')
    $SummaryLines.Add('Stop acceptance: PASS')
    $SummaryLines.Add('Full local audit: PASS')
    $SummaryLines.Add('Repository-owned Playwright proof: PASS')
    $SummaryLines.Add('Downloads auto-opened: NO')
    $SummaryLines.Add('')
    $SummaryLines.Add('EVIDENCE PACKAGES')
    foreach ($Record in $EvidenceRecords) {
        $SummaryLines.Add($Record.name)
        $SummaryLines.Add(('  SHA-256: ' + $Record.sha256))
        $SummaryLines.Add(('  Size: ' + $Record.size_bytes + ' bytes'))
    }
    $SummaryLines | Out-File -LiteralPath $SummaryPath -Encoding utf8

    [pscustomobject]@{
        schema_version = 3
        generated_at = $CompletedAt.ToString('o')
        status = 'PASS'
        repository_url = $RepositoryUrl
        branch = $Branch
        head_sha = $HeadSha
        launcher_acceptance = $true
        stop_acceptance = $true
        full_local_audit = $true
        playwright_proof = $true
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
}
catch {
    $FailureMessage = $_.Exception.Message
    if (-not (Test-Path -LiteralPath $EvidenceRoot)) {
        New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null
    }

    @(
        'CUSTOSOPS V1 CLEAN-MACHINE ACCEPTANCE',
        ('Generated: ' + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz')),
        'Status: FAIL',
        ('Repository: ' + $RepositoryUrl),
        ('Branch: ' + $Branch),
        ('Fresh-clone HEAD: ' + $HeadSha),
        '',
        'FAILURE',
        $FailureMessage
    ) | Out-File -LiteralPath $SummaryPath -Encoding utf8

    if ($OutputDir -and (Test-Path -LiteralPath $OutputDir)) {
        $FinalZip = Join-Path $OutputDir ('CUSTOSOPS_V1_ACCEPTANCE_FAILED_' + $Stamp + '.zip')
        if (Test-Path -LiteralPath $FinalZip) { Remove-Item -LiteralPath $FinalZip -Force }
        Compress-Archive -Path (Join-Path $EvidenceRoot '*') -DestinationPath $FinalZip -Force
    }

    Write-Host ''
    Write-Host ('CUSTOSOPS V1 CLEAN-MACHINE ACCEPTANCE: FAIL - ' + $FailureMessage) -ForegroundColor Red
    if ($FinalZip) { Write-Host ('Failure evidence ZIP: ' + $FinalZip) -ForegroundColor Yellow }
}
finally {
    try {
        if (Test-Path -LiteralPath $CloneRoot) { Stop-FreshCustosOps -RootPath $CloneRoot }
    }
    catch {}

    Set-Location $StartLocation
    if (-not $KeepFreshClone -and (Test-Path -LiteralPath $FreshRoot)) {
        try { Remove-Item -LiteralPath $FreshRoot -Recurse -Force } catch {}
    }
}

if ($FailureMessage) { exit 1 }
exit 0
