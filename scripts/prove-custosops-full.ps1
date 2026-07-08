<#
CustosOps Full Proof Runner

Runs the repository audit and, when required, the external Desktop UI proof tool.
This script does not modify source files.
#>

param(
    [string]$Root = '.',
    [string]$OutputDir = '',
    [string]$UiProofScript = '',
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

Write-Host ''
Write-Host 'CustosOps full proof runner' -ForegroundColor Cyan
Write-Host ('Repository: ' + $RootPath)
Write-Host ('OutputDir:  ' + $OutputDir)
Write-Host ''

if (-not (Test-Path -LiteralPath $AuditScript)) {
    Set-Failed ('ERROR: Local audit script not found: ' + $AuditScript)
}
else {
    Write-Host 'Step 1/2: Running full local repository audit...' -ForegroundColor Cyan
    & $AuditScript -Root $RootPath -OutputDir $OutputDir -RunExistingContractAudits -RunBackendTests -RunFrontendBuild
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
    else {
        Write-Host 'Step 2/2: Running Desktop UI proof...' -ForegroundColor Cyan
        $BeforeProofZips = @(Get-ChildItem -LiteralPath $OutputDir -Filter 'CUSTOSOPS_UI_SMOKE_*.zip' -File -ErrorAction SilentlyContinue | ForEach-Object { $_.FullName })

        powershell.exe -NoProfile -ExecutionPolicy Bypass -File $UiProofScript
        $UiProofExit = $LASTEXITCODE
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
            Write-Host ('Desktop UI proof ZIP: ' + $LatestProofZip.FullName)
            & $ProofChecker -ZipPath $LatestProofZip.FullName
            $ProofCheckExit = $LASTEXITCODE
            if ($ProofCheckExit -ne 0) {
                Set-Failed ('Desktop UI proof artifact check failed with exit code ' + $ProofCheckExit)
            }
            else {
                Write-Host 'Desktop UI proof artifact check: OK' -ForegroundColor Green
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
