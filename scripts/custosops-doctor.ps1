param(
    [switch]$SkipValidation,
    [switch]$Full
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $Root

$Failed = $false

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host ("== " + $Message + " ==")
}

function Mark-Failed {
    param([string]$Message)
    Write-Host ("FAILED: " + $Message)
    $script:Failed = $true
}

Write-Step "CustosOps doctor"
Write-Host ("Root: " + $Root)

Write-Step "Required files"
$Required = @(
    "LAUNCH_CUSTOSOPS.bat",
    "STOP_CUSTOSOPS.bat",
    "scripts\validate-foundation.ps1",
    "scripts\custosops-release-smoke.py",
    "backend\app\main.py",
    "backend\requirements.txt",
    "frontend\package.json",
    "frontend\src\App.tsx"
)

foreach ($item in $Required) {
    $path = Join-Path $Root $item
    if (Test-Path -LiteralPath $path) {
        Write-Host ("OK: " + $item)
    } else {
        Mark-Failed ("Missing " + $item)
    }
}

Write-Step "Tool versions"
try { python --version } catch { Mark-Failed "python not available" }
try { node --version } catch { Mark-Failed "node not available" }
try { npm.cmd --version } catch { Mark-Failed "npm.cmd not available" }
try { git --version } catch { Mark-Failed "git not available" }

Write-Step "Local dependency folders"
if (Test-Path -LiteralPath "$Root\backend\.venv\Scripts\python.exe") {
    Write-Host "OK: backend virtual environment exists"
} else {
    Mark-Failed "backend virtual environment missing"
}

if (Test-Path -LiteralPath "$Root\frontend\node_modules") {
    Write-Host "OK: frontend node_modules exists"
} else {
    Mark-Failed "frontend node_modules missing"
}

Write-Step "Git status"
git status --short

if (-not $SkipValidation) {
    Write-Step "Foundation validation"
    & "$Root\scripts\validate-foundation.ps1"
    if ($LASTEXITCODE -ne 0) {
        Mark-Failed "foundation validation failed"
    }
}

if ($Full) {
    Write-Step "Release smoke"
    $SmokeOut = Join-Path $env:TEMP ("CUSTOSOPS_DOCTOR_SMOKE_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
    & "$Root\backend\.venv\Scripts\python.exe" "$Root\scripts\custosops-release-smoke.py" $SmokeOut
    if ($LASTEXITCODE -ne 0) {
        Mark-Failed "release smoke failed"
    } else {
        Write-Host ("Release smoke output: " + $SmokeOut)
    }
}

Write-Step "Doctor result"
if ($Failed) {
    Write-Host "CustosOps doctor found problems."
    exit 1
}

Write-Host "CustosOps doctor completed successfully."
exit 0
