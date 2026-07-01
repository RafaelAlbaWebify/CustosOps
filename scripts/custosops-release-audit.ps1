param(
    [switch]$SkipValidation
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Desktop = [Environment]::GetFolderPath('Desktop')
$Downloads = Join-Path $env:USERPROFILE 'Downloads'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$AuditRoot = Join-Path $env:TEMP ("CUSTOSOPS_RELEASE_AUDIT_" + $Stamp)
$DesktopZip = Join-Path $Desktop ("CUSTOSOPS_RELEASE_AUDIT_" + $Stamp + ".zip")
$DownloadsZip = Join-Path $Downloads ("CUSTOSOPS_RELEASE_AUDIT_" + $Stamp + ".zip")

Set-Location -LiteralPath $Root

New-Item -ItemType Directory -Force -Path $AuditRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $AuditRoot 'logs') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $AuditRoot 'project_copy') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $AuditRoot 'release_reports') | Out-Null

function Write-TextFile {
    param(
        [string]$Path,
        [string]$Content
    )

    $dir = Split-Path -Parent $Path

    if ($dir -and !(Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    [System.IO.File]::WriteAllText($Path, $Content, [System.Text.Encoding]::UTF8)
}

function Run-Capture {
    param(
        [string]$Name,
        [scriptblock]$Block
    )

    $Path = Join-Path $AuditRoot ("logs\" + $Name + ".txt")

    try {
        $output = & $Block 2>&1 | Out-String
        Write-TextFile -Path $Path -Content $output
    } catch {
        Write-TextFile -Path $Path -Content ("ERROR: " + $_.Exception.Message)
    }
}

function Copy-IfExists {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (Test-Path -LiteralPath $Source) {
        $parent = Split-Path -Parent $Destination

        if ($parent -and !(Test-Path -LiteralPath $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }

        Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
    }
}

Write-TextFile -Path (Join-Path $AuditRoot 'README_RELEASE_AUDIT.txt') -Content @"
CustosOps release audit
Generated: $(Get-Date -Format o)
Project root: $Root
Desktop ZIP: $DesktopZip
Downloads ZIP: $DownloadsZip

Purpose:
Release checkpoint after Operational Intelligence Pack and Executive Summary Pack.
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

Run-Capture -Name '03_git_diff' -Block {
    git diff --stat
    ""
    git diff --name-status
    ""
    git diff -- .
}

if (-not $SkipValidation) {
    Run-Capture -Name '04_validation' -Block {
        Set-Location -LiteralPath $Root
        .\scripts\validate-foundation.ps1
    }
}

Run-Capture -Name '05_release_smoke_reports' -Block {
    Set-Location -LiteralPath $Root
    & "$Root\backend\.venv\Scripts\python.exe" "$Root\scripts\custosops-release-smoke.py" (Join-Path $AuditRoot 'release_reports')
}

Run-Capture -Name '06_backend_routes' -Block {
    Select-String -Path "$Root\backend\app\api\*.py","$Root\backend\app\main.py" -Pattern "executive|windows|endpoint|dns|app-log|archive|router|include_router|@router" -CaseSensitive:$false -Context 2,2
}

Run-Capture -Name '07_frontend_reports_search' -Block {
    Select-String -Path "$Root\frontend\src\App.tsx" -Pattern "Executive Summary Pack|ReportsWorkspace|ReportCard|handleExecutiveSummary|buildExecutiveSummary|executiveReady|onExecutiveDownload" -CaseSensitive:$false -Context 4,4
}

Run-Capture -Name '08_archive_manifest' -Block {
    $manifest = "$Root\reports\custosops_archive\manifest.json"

    if (Test-Path -LiteralPath $manifest) {
        Get-Content -LiteralPath $manifest
    } else {
        "Archive manifest not found."
    }
}

Run-Capture -Name '09_archive_files' -Block {
    if (Test-Path -LiteralPath "$Root\reports\custosops_archive") {
        Get-ChildItem -LiteralPath "$Root\reports\custosops_archive" -Recurse -File |
            Select-Object FullName, Length, LastWriteTime |
            Sort-Object LastWriteTime -Descending |
            Format-Table -AutoSize
    } else {
        "Archive folder not found."
    }
}

Run-Capture -Name '10_ports_processes' -Block {
    "Port 8000:"
    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Format-Table -AutoSize
    ""
    "Port 5173:"
    Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | Format-Table -AutoSize
    ""
    "Node/Python processes:"
    Get-Process node, python, python3, uvicorn -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, Path, StartTime | Format-Table -AutoSize
}

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
    Copy-IfExists -Source (Join-Path $Root $dir) -Destination (Join-Path (Join-Path $AuditRoot 'project_copy') $dir)
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
    Copy-IfExists -Source (Join-Path $Root $file) -Destination (Join-Path (Join-Path $AuditRoot 'project_copy') $file)
}

Run-Capture -Name '99_audit_bundle_contents' -Block {
    Get-ChildItem -LiteralPath $AuditRoot -Recurse -File |
        Select-Object FullName, Length |
        Sort-Object FullName |
        Format-Table -AutoSize
}

if (Test-Path -LiteralPath $DesktopZip) {
    Remove-Item -LiteralPath $DesktopZip -Force
}

Compress-Archive -Path (Join-Path $AuditRoot '*') -DestinationPath $DesktopZip -Force

if (Test-Path -LiteralPath $DownloadsZip) {
    Remove-Item -LiteralPath $DownloadsZip -Force
}

Copy-Item -LiteralPath $DesktopZip -Destination $DownloadsZip -Force

Write-Host ""
Write-Host "Release audit ZIP created:"
Write-Host $DesktopZip
Write-Host ""
Write-Host "Copied to:"
Write-Host $DownloadsZip
Write-Host ""

explorer.exe /select,"$DesktopZip"
