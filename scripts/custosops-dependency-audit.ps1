param(
    [string]$OutputRoot,
    [switch]$TrySafeNpmFix
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location -LiteralPath $Root

if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $OutputRoot = Join-Path $Root ("reports\dependency_audit\" + $Stamp)
}

New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

function Write-TextFile {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Parent $Path
    if ($dir -and !(Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.Encoding]::UTF8)
}

function Run-Capture {
    param([string]$Name, [scriptblock]$Block)
    $Path = Join-Path $OutputRoot ($Name + ".txt")
    try {
        $output = & $Block 2>&1 | Out-String
        Write-TextFile -Path $Path -Content $output
    } catch {
        Write-TextFile -Path $Path -Content ("ERROR: " + $_.Exception.Message)
    }
}

Write-TextFile -Path (Join-Path $OutputRoot "README_DEPENDENCY_AUDIT.txt") -Content @"
CustosOps dependency audit
Generated: $(Get-Date -Format o)
Project root: $Root

This audit is local evidence only.
No forced dependency upgrade is performed.
"@

Run-Capture -Name "00_versions" -Block {
    "Python:"
    python --version
    ""
    "Node:"
    node --version
    ""
    "NPM:"
    npm.cmd --version
    ""
    "Git:"
    git --version
}

Run-Capture -Name "01_pip_check" -Block {
    if (Test-Path -LiteralPath "$Root\backend\.venv\Scripts\python.exe") {
        & "$Root\backend\.venv\Scripts\python.exe" -m pip check
    } else {
        "backend venv not found"
    }
}

Run-Capture -Name "02_pip_freeze" -Block {
    if (Test-Path -LiteralPath "$Root\backend\.venv\Scripts\python.exe") {
        & "$Root\backend\.venv\Scripts\python.exe" -m pip freeze
    } else {
        "backend venv not found"
    }
}

Run-Capture -Name "03_npm_ls_depth0" -Block {
    Set-Location -LiteralPath "$Root\frontend"
    npm.cmd ls --depth=0
}

Run-Capture -Name "04_npm_audit" -Block {
    Set-Location -LiteralPath "$Root\frontend"
    npm.cmd audit
}

Run-Capture -Name "05_npm_audit_json" -Block {
    Set-Location -LiteralPath "$Root\frontend"
    npm.cmd audit --json
}

if ($TrySafeNpmFix) {
    Run-Capture -Name "06_npm_audit_fix_no_force" -Block {
        Set-Location -LiteralPath "$Root\frontend"
        npm.cmd audit fix
        ""
        "Exit code: " + $LASTEXITCODE
    }
}

Write-Host ""
Write-Host "Dependency audit output:"
Write-Host $OutputRoot
Write-Host ""
exit 0
