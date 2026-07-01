param(
    [switch]$SkipValidation
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Desktop = [Environment]::GetFolderPath('Desktop')
$Downloads = Join-Path $env:USERPROFILE 'Downloads'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$PackageRoot = Join-Path $env:TEMP ("CUSTOSOPS_LOCAL_PACKAGE_" + $Stamp)
$DesktopZip = Join-Path $Desktop ("CUSTOSOPS_LOCAL_PACKAGE_" + $Stamp + ".zip")
$DownloadsZip = Join-Path $Downloads ("CUSTOSOPS_LOCAL_PACKAGE_" + $Stamp + ".zip")

Set-Location -LiteralPath $Root

New-Item -ItemType Directory -Force -Path $PackageRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot 'metadata') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot 'source') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $PackageRoot 'dependency_audit') | Out-Null

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
    $Path = Join-Path $PackageRoot ("metadata\" + $Name + ".txt")
    try {
        $output = & $Block 2>&1 | Out-String
        Write-TextFile -Path $Path -Content $output
    } catch {
        Write-TextFile -Path $Path -Content ("ERROR: " + $_.Exception.Message)
    }
}

function Copy-IfExists {
    param([string]$Source, [string]$Destination)
    if (Test-Path -LiteralPath $Source) {
        $parent = Split-Path -Parent $Destination
        if ($parent -and !(Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
    }
}

Write-TextFile -Path (Join-Path $PackageRoot 'README_LOCAL_PACKAGE.txt') -Content @"
CustosOps local package
Generated: $(Get-Date -Format o)
Project root: $Root

This package contains source, docs, samples, scripts, and metadata.
It intentionally excludes node_modules, backend virtual environment, frontend dist, git internals, report archive contents, and caches.

To run from a cloned or unpacked project:
1. Open PowerShell.
2. Set-Location to the project root.
3. Run .\scripts\validate-foundation.ps1
4. Run .\LAUNCH_CUSTOSOPS.bat
"@

Run-Capture -Name '00_git_status' -Block {
    git status --short
    ""
    git status
}

Run-Capture -Name '01_git_log' -Block {
    git --no-pager log --oneline -25
}

Run-Capture -Name '02_git_tags' -Block {
    git tag --list --sort=-creatordate
}

Run-Capture -Name '03_versions' -Block {
    python --version
    node --version
    npm.cmd --version
    git --version
}

if (-not $SkipValidation) {
    Run-Capture -Name '04_validation' -Block {
        Set-Location -LiteralPath $Root
        .\scripts\validate-foundation.ps1
    }
}

Run-Capture -Name '05_release_smoke' -Block {
    Set-Location -LiteralPath $Root
    $SmokeOut = Join-Path $PackageRoot 'release_smoke'
    & "$Root\backend\.venv\Scripts\python.exe" "$Root\scripts\custosops-release-smoke.py" $SmokeOut
}

& "$Root\scripts\custosops-dependency-audit.ps1" -OutputRoot (Join-Path $PackageRoot 'dependency_audit') | Out-Null

$DirsToCopy = @(
    'backend\app',
    'backend\tests',
    'frontend\src',
    'docs',
    'samples',
    'scripts',
    'collectors'
)

foreach ($dir in $DirsToCopy) {
    Copy-IfExists -Source (Join-Path $Root $dir) -Destination (Join-Path (Join-Path $PackageRoot 'source') $dir)
}

$FilesToCopy = @(
    '.gitignore',
    'README.md',
    'LAUNCH_CUSTOSOPS.bat',
    'STOP_CUSTOSOPS.bat',
    'backend\requirements.txt',
    'frontend\package.json',
    'frontend\package-lock.json',
    'frontend\tsconfig.json',
    'frontend\vite.config.ts',
    'reports\custosops_archive\manifest.json'
)

foreach ($file in $FilesToCopy) {
    Copy-IfExists -Source (Join-Path $Root $file) -Destination (Join-Path (Join-Path $PackageRoot 'source') $file)
}

Run-Capture -Name '99_package_contents' -Block {
    Get-ChildItem -LiteralPath $PackageRoot -Recurse -File |
        Select-Object FullName, Length |
        Sort-Object FullName |
        Format-Table -AutoSize
}

if (Test-Path -LiteralPath $DesktopZip) {
    Remove-Item -LiteralPath $DesktopZip -Force
}

Compress-Archive -Path (Join-Path $PackageRoot '*') -DestinationPath $DesktopZip -Force

if (Test-Path -LiteralPath $DownloadsZip) {
    Remove-Item -LiteralPath $DownloadsZip -Force
}

Copy-Item -LiteralPath $DesktopZip -Destination $DownloadsZip -Force

Write-Host ""
Write-Host "Local package ZIP created:"
Write-Host $DesktopZip
Write-Host ""
Write-Host "Copied to:"
Write-Host $DownloadsZip
Write-Host ""

explorer.exe /select,"$DesktopZip"
