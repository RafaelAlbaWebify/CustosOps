param(
    [string]$Root = "",
    [string]$OutputDir = "",
    [string]$StatusFile = ""
)

$AuditOk = $true
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

if (-not $Root) {
    $Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if (-not $OutputDir) {
    $OutputDir = Join-Path $env:USERPROFILE "Downloads"
}

$AuditDir = Join-Path $OutputDir ("CUSTOSOPS_EVIDENCE_CONTRACT_AUDIT_" + $Stamp)
$AuditZip = $AuditDir + ".zip"
New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null

function Add-Line {
    param([string]$Line)
    $script:Lines.Add($Line) | Out-Null
}

function Add-Fail {
    param([string]$Message)
    $script:AuditOk = $false
    Add-Line ("FAILED: " + $Message)
}

function Add-Ok {
    param([string]$Message)
    Add-Line ("OK: " + $Message)
}

function Test-FileRequired {
    param([string]$RelativePath)
    $Path = Join-Path $Root $RelativePath
    if (Test-Path -LiteralPath $Path) {
        Add-Ok ("file exists: " + $RelativePath)
    }
    else {
        Add-Fail ("missing file: " + $RelativePath)
    }
}

function Test-PatternRequired {
    param(
        [string]$RelativePath,
        [string]$Pattern,
        [string]$Description
    )
    $Path = Join-Path $Root $RelativePath
    if (-not (Test-Path -LiteralPath $Path)) {
        Add-Fail ("cannot check missing file: " + $RelativePath)
        return
    }
    $Text = Get-Content -LiteralPath $Path -Raw
    if ($Text -match $Pattern) {
        Add-Ok ($Description + " in " + $RelativePath)
    }
    else {
        Add-Fail ($Description + " missing in " + $RelativePath)
    }
}

$Lines = New-Object System.Collections.Generic.List[string]
Add-Line "# CustosOps Evidence Module Contract Audit"
Add-Line ""
Add-Line ("Root: " + $Root)
Add-Line ("Generated: " + (Get-Date).ToString("s"))
Add-Line ""

$RequiredFiles = @(
    "docs/architecture/EVIDENCE_MODULE_HELPER_CONTRACT.md",
    "docs/architecture/PLATFORM_MODULE_CONTRACT.md",
    "backend/app/schemas/finding.py",
    "backend/app/schemas/evidence_run.py",
    "backend/app/services/evidence_run_history.py",
    "backend/app/services/report_archive.py",
    "backend/app/services/redaction_engine.py",
    "backend/app/api/evidence_runs.py",
    "frontend/src/App.tsx",
    "frontend/src/components/RunHistoryWorkspace.tsx"
)

Add-Line "## Required shared files"
foreach ($File in $RequiredFiles) {
    Test-FileRequired -RelativePath $File
}
Add-Line ""

$Modules = @(
    "endpoint|backend/app/schemas/endpoint.py|backend/app/api/endpoint.py|backend/app/analyzers/endpoint_security.py|backend/app/services/endpoint_report.py|backend/tests/test_endpoint_report.py",
    "dns|backend/app/schemas/dns.py|backend/app/api/dns.py|backend/app/analyzers/dns_hygiene.py|backend/app/services/dns_report.py|backend/tests/test_dns_report.py",
    "app-log|backend/app/schemas/app_log.py|backend/app/api/app_log.py|backend/app/analyzers/app_log_evidence.py|backend/app/services/app_log_report.py|backend/tests/test_app_log_evidence.py",
    "windows-events|backend/app/schemas/windows_event.py|backend/app/api/windows_events.py|backend/app/analyzers/windows_event_evidence.py|backend/app/services/windows_event_report.py|backend/tests/test_windows_event_evidence.py",
    "iis|backend/app/schemas/iis.py|backend/app/api/iis.py|backend/app/analyzers/iis_evidence.py|backend/app/services/iis_report.py|backend/tests/test_iis_evidence.py"
)

Add-Line "## Module file coverage"
foreach ($ModuleSpec in $Modules) {
    $Parts = $ModuleSpec.Split("|")
    Add-Line ("### " + $Parts[0])
    for ($i = 1; $i -lt $Parts.Count; $i++) {
        Test-FileRequired -RelativePath $Parts[$i]
    }
    Add-Line ""
}

Add-Line "## Shared contract pattern checks"
Test-PatternRequired -RelativePath "backend/app/schemas/finding.py" -Pattern "class SecurityFinding" -Description "SecurityFinding schema"
Test-PatternRequired -RelativePath "backend/app/schemas/finding.py" -Pattern "class EvidenceItem" -Description "EvidenceItem schema"
Test-PatternRequired -RelativePath "backend/app/schemas/evidence_run.py" -Pattern "class EvidenceRunCreateRequest" -Description "EvidenceRunCreateRequest schema"
Test-PatternRequired -RelativePath "backend/app/schemas/evidence_run.py" -Pattern "class EvidenceRunRecord" -Description "EvidenceRunRecord schema"
Test-PatternRequired -RelativePath "backend/app/services/evidence_run_history.py" -Pattern "def record_evidence_run" -Description "run history recorder"
Test-PatternRequired -RelativePath "backend/app/services/report_archive.py" -Pattern "def save_archived_report" -Description "archive save helper"
Test-PatternRequired -RelativePath "backend/app/services/redaction_engine.py" -Pattern "def redact" -Description "redaction helper"
Test-PatternRequired -RelativePath "frontend/src/App.tsx" -Pattern "loadRunHistory" -Description "frontend run history lifecycle"
Test-PatternRequired -RelativePath "frontend/src/App.tsx" -Pattern "handleReportDownload" -Description "frontend report workflow"
Test-PatternRequired -RelativePath "frontend/src/components/RunHistoryWorkspace.tsx" -Pattern "export function RunHistoryWorkspace" -Description "Run History workspace component"
Add-Line ""

Add-Line "## Report builder checks"
Test-PatternRequired -RelativePath "backend/app/services/endpoint_report.py" -Pattern "def build_endpoint_report" -Description "endpoint report builder"
Test-PatternRequired -RelativePath "backend/app/services/dns_report.py" -Pattern "def build_dns_report" -Description "dns report builder"
Test-PatternRequired -RelativePath "backend/app/services/app_log_report.py" -Pattern "def build_app_log_report" -Description "app-log report builder"
Test-PatternRequired -RelativePath "backend/app/services/windows_event_report.py" -Pattern "def build_windows_event_report" -Description "windows-events report builder"
Test-PatternRequired -RelativePath "backend/app/services/iis_report.py" -Pattern "def build_iis_report" -Description "iis report builder"
Test-PatternRequired -RelativePath "backend/app/services/endpoint_report.py" -Pattern "content_type" -Description "endpoint content type"
Test-PatternRequired -RelativePath "backend/app/services/dns_report.py" -Pattern "content_type" -Description "dns content type"
Test-PatternRequired -RelativePath "backend/app/services/app_log_report.py" -Pattern "content_type" -Description "app-log content type"
Test-PatternRequired -RelativePath "backend/app/services/windows_event_report.py" -Pattern "content_type" -Description "windows-events content type"
Test-PatternRequired -RelativePath "backend/app/services/iis_report.py" -Pattern "content_type" -Description "iis content type"
Add-Line ""

Add-Line "## Analyzer checks"
Test-PatternRequired -RelativePath "backend/app/analyzers/endpoint_security.py" -Pattern "analyze_endpoint_evidence" -Description "endpoint analyzer"
Test-PatternRequired -RelativePath "backend/app/analyzers/dns_hygiene.py" -Pattern "analyze_dns_evidence" -Description "dns analyzer"
Test-PatternRequired -RelativePath "backend/app/analyzers/app_log_evidence.py" -Pattern "analyze_app_log_evidence" -Description "app-log analyzer"
Test-PatternRequired -RelativePath "backend/app/analyzers/windows_event_evidence.py" -Pattern "analyze_windows_event_evidence" -Description "windows-events analyzer"
Test-PatternRequired -RelativePath "backend/app/analyzers/iis_evidence.py" -Pattern "analyze_iis_evidence" -Description "iis analyzer"
Add-Line ""

if ($AuditOk) {
    Add-Line "RESULT: OK"
}
else {
    Add-Line "RESULT: FAILED"
}

$ReportPath = Join-Path $AuditDir "EVIDENCE_MODULE_CONTRACT_AUDIT.md"
Set-Content -LiteralPath $ReportPath -Value $Lines.ToArray() -Encoding ASCII

$SnapshotFiles = @(
    "docs/architecture/EVIDENCE_MODULE_HELPER_CONTRACT.md",
    "docs/architecture/PLATFORM_MODULE_CONTRACT.md",
    "backend/app/schemas/finding.py",
    "backend/app/schemas/evidence_run.py",
    "backend/app/services/evidence_run_history.py",
    "frontend/src/App.tsx",
    "frontend/src/components/RunHistoryWorkspace.tsx"
)

foreach ($Snapshot in $SnapshotFiles) {
    $Source = Join-Path $Root $Snapshot
    if (Test-Path -LiteralPath $Source) {
        $Name = "source_snapshot_" + ($Snapshot.Replace("/", "_").Replace("\", "_"))
        Copy-Item -LiteralPath $Source -Destination (Join-Path $AuditDir $Name) -Force
    }
}

if ($StatusFile) {
    if ($AuditOk) {
        Set-Content -LiteralPath $StatusFile -Value "OK" -Encoding ASCII
    }
    else {
        Set-Content -LiteralPath $StatusFile -Value "FAILED" -Encoding ASCII
    }
}

if (Test-Path -LiteralPath $AuditZip) {
    Remove-Item -LiteralPath $AuditZip -Force
}

Compress-Archive -Path (Join-Path $AuditDir "*") -DestinationPath $AuditZip -Force
Write-Host "Evidence contract audit ZIP:"
Write-Host $AuditZip

if ($AuditOk) {
    Write-Host "Evidence contract audit: OK" -ForegroundColor Green
}
else {
    Write-Host "Evidence contract audit: FAILED" -ForegroundColor Red
}

$AuditOk

