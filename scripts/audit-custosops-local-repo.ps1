<#
CustosOps Local Repository Audit
Read-only audit for the local working copy.

Purpose:
- Check local Git state, required files, generated artifacts, public-safety risks, and validation command results.
- Create a ZIP proof package in Downloads by default.
- Never modify source files.
#>

param(
    [string]$Root = '.',
    [string]$OutputDir = '',
    [switch]$RunBackendTests,
    [switch]$RunFrontendBuild,
    [switch]$RunExistingContractAudits
)

$ErrorActionPreference = 'Continue'
$AuditOk = $true
$Findings = New-Object System.Collections.Generic.List[object]
$Lines = New-Object System.Collections.Generic.List[string]

function Add-Line {
    param([string]$Text)
    $script:Lines.Add($Text) | Out-Null
}

function Add-Finding {
    param(
        [string]$Severity,
        [string]$Area,
        [string]$Message,
        [string]$Evidence = ''
    )
    if ($Severity -in @('HIGH', 'CRITICAL')) { $script:AuditOk = $false }
    $script:Findings.Add([pscustomobject]@{
        severity = $Severity
        area = $Area
        message = $Message
        evidence = $Evidence
    }) | Out-Null
}

function Write-Utf8NoBom {
    param([string]$Path, [string]$Text)
    $Encoding = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $Encoding)
}

function Resolve-RepoRoot {
    param([string]$Path)
    try {
        return (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
    }
    catch {
        Write-Host 'ERROR: Root path not found.' -ForegroundColor Red
        exit 1
    }
}

function Invoke-AuditCommand {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDirectory,
        [int]$TimeoutSeconds = 240
    )

    $SafeName = $Name -replace '[^a-zA-Z0-9_.-]', '_'
    $OutFile = Join-Path $script:AuditDir ('command_' + $SafeName + '.txt')

    Add-Line ''
    Add-Line ('### ' + $Name)
    Add-Line ''
    Add-Line '```text'
    Add-Line $Command
    Add-Line '```'

    try {
        $Psi = New-Object System.Diagnostics.ProcessStartInfo
        $Psi.FileName = 'powershell.exe'
        $Psi.Arguments = '-NoProfile -ExecutionPolicy Bypass -Command ' + [char]34 + $Command + [char]34
        $Psi.WorkingDirectory = $WorkingDirectory
        $Psi.RedirectStandardOutput = $true
        $Psi.RedirectStandardError = $true
        $Psi.UseShellExecute = $false
        $Psi.CreateNoWindow = $true

        $Process = New-Object System.Diagnostics.Process
        $Process.StartInfo = $Psi
        [void]$Process.Start()

        if (-not $Process.WaitForExit($TimeoutSeconds * 1000)) {
            try { $Process.Kill() } catch {}
            Write-Utf8NoBom -Path $OutFile -Text ('TIMEOUT after ' + $TimeoutSeconds + ' seconds.')
            Add-Line 'Result: TIMEOUT'
            Add-Finding -Severity 'MEDIUM' -Area 'command' -Message ($Name + ' timed out') -Evidence $Command
            return
        }

        $StdOut = $Process.StandardOutput.ReadToEnd()
        $StdErr = $Process.StandardError.ReadToEnd()
        $Text = 'EXIT_CODE: ' + $Process.ExitCode + "`r`n`r`nSTDOUT:`r`n" + $StdOut + "`r`nSTDERR:`r`n" + $StdErr
        Write-Utf8NoBom -Path $OutFile -Text $Text
        Add-Line ('Result: exit code ' + $Process.ExitCode)

        if ($Process.ExitCode -ne 0) {
            Add-Finding -Severity 'HIGH' -Area 'command' -Message ($Name + ' returned a non-zero exit code') -Evidence ('Exit code ' + $Process.ExitCode)
        }
    }
    catch {
        Write-Utf8NoBom -Path $OutFile -Text $_.Exception.Message
        Add-Line ('Result: ERROR - ' + $_.Exception.Message)
        Add-Finding -Severity 'HIGH' -Area 'command' -Message ($Name + ' failed to run') -Evidence $_.Exception.Message
    }
}

function Test-RequiredFile {
    param([string]$RelativePath)
    $Path = Join-Path $script:RootPath $RelativePath
    if (Test-Path -LiteralPath $Path) {
        Add-Line ('| ' + $RelativePath + ' | OK | |')
    }
    else {
        Add-Line ('| ' + $RelativePath + ' | MISSING | Required file not found. |')
        Add-Finding -Severity 'HIGH' -Area 'required-file' -Message 'Missing required file' -Evidence $RelativePath
    }
}

function Get-RepoFiles {
    param([string]$RepoRoot)
    if (Get-Command git.exe -ErrorAction SilentlyContinue) {
        $GitFiles = & git -C $RepoRoot ls-files 2>$null
        if ($LASTEXITCODE -eq 0 -and $GitFiles) { return @($GitFiles) }
    }

    $Excluded = @('.git', '.venv', 'node_modules', 'dist', 'build', '__pycache__', '.pytest_cache')
    return @(Get-ChildItem -LiteralPath $RepoRoot -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
        $Full = $_.FullName
        $Keep = $true
        foreach ($Dir in $Excluded) {
            if ($Full -like ('*\' + $Dir + '\*')) { $Keep = $false }
        }
        $Keep
    } | ForEach-Object { $_.FullName.Substring($RepoRoot.Length).TrimStart('\','/') })
}

function Test-SafetyScanIgnore {
    param(
        [string]$RelativePath,
        [string]$CheckName,
        [string]$Line
    )

    if ($RelativePath -eq 'scripts/audit-custosops-local-repo.ps1' -and $Line -match ('^\s*' + [regex]::Escape($CheckName) + '\s*=')) {
        return $true
    }

    if ($CheckName -eq 'secret_assignment' -and $RelativePath -match '(?i)redaction') {
        return $true
    }

    return $false
}

function Search-PublicSafetyHits {
    param([string[]]$Files)

    $Patterns = [ordered]@{
        workplace_name = '(?i)(faurecia|forvia|stellantis|quental)'
        secret_assignment = '(?i)(password|passwd|secret|token|apikey|api_key|client_secret)\s*[:=]\s*["'']?[^"''\s]{8,}'
        windows_user_path = 'C:\\Users\\[^\\\s]+'
        private_ipv4 = '\b(?:10|172\.(?:1[6-9]|2[0-9]|3[0-1])|192\.168)\.\d{1,3}\.\d{1,3}\b'
        email_address = '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
        offensive_wording = '(?i)(exploit|payload|reverse shell|bypass authentication|privilege escalation|pentest|penetration test)'
    }

    $BlockingChecks = @('workplace_name', 'secret_assignment')
    $TextExtensions = @('.md', '.txt', '.ps1', '.py', '.ts', '.tsx', '.js', '.json', '.css', '.bat', '.yml', '.yaml', '.html', '.csv')
    $Hits = @()

    foreach ($Rel in $Files) {
        $Full = Join-Path $script:RootPath $Rel
        if (-not (Test-Path -LiteralPath $Full)) { continue }
        $Ext = [System.IO.Path]::GetExtension($Full).ToLowerInvariant()
        if ($TextExtensions -notcontains $Ext) { continue }

        try { $Text = Get-Content -LiteralPath $Full -Raw -Encoding UTF8 -ErrorAction Stop }
        catch { try { $Text = Get-Content -LiteralPath $Full -Raw -ErrorAction Stop } catch { continue } }

        $LineNumber = 0
        foreach ($Line in ($Text -split "`r?`n")) {
            $LineNumber += 1
            foreach ($Name in $Patterns.Keys) {
                if ($Line -notmatch $Patterns[$Name]) { continue }
                if (Test-SafetyScanIgnore -RelativePath $Rel -CheckName $Name -Line $Line) { continue }

                $BlocksPublication = $BlockingChecks -contains $Name
                $Severity = 'REVIEW'
                if ($BlocksPublication) { $Severity = 'HIGH' }

                $Hits += [pscustomobject]@{
                    file = $Rel
                    line = $LineNumber
                    check = $Name
                    severity = $Severity
                    blocks_publication = $BlocksPublication
                    note = 'Match content intentionally omitted from audit artifact. Review the source file locally.'
                }

                if ($BlocksPublication) {
                    Add-Finding -Severity 'HIGH' -Area 'public-safety-scan' -Message ('Blocking text scan hit: ' + $Name) -Evidence ($Rel + ':' + $LineNumber)
                }
            }
        }
    }

    return $Hits
}

$RootPath = Resolve-RepoRoot -Path $Root
if (-not $OutputDir) {
    if ($env:USERPROFILE) { $OutputDir = Join-Path $env:USERPROFILE 'Downloads' }
    else { $OutputDir = [Environment]::GetFolderPath('UserProfile') }
}
if (-not (Test-Path -LiteralPath $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }

$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$AuditDir = Join-Path $OutputDir ('CUSTOSOPS_LOCAL_REPO_AUDIT_' + $Stamp)
$AuditZip = $AuditDir + '.zip'
New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null

Add-Line '# CustosOps Local Repository Audit'
Add-Line ''
Add-Line ('Generated: ' + (Get-Date).ToString('s'))
Add-Line ('Root: ' + $RootPath)
Add-Line ''
Add-Line 'This audit is read-only. It validates local repo state, safety, and portfolio readiness before public/demo review.'

Add-Line ''
Add-Line '## Git state'
Add-Line ''
if (Get-Command git.exe -ErrorAction SilentlyContinue) {
    $Branch = & git -C $RootPath rev-parse --abbrev-ref HEAD 2>$null
    $Head = & git -C $RootPath rev-parse HEAD 2>$null
    $Tag = & git -C $RootPath describe --tags --abbrev=0 2>$null
    $Status = @(& git -C $RootPath status --short 2>$null)
    $Recent = @(& git -C $RootPath log --oneline -n 10 2>$null)

    Add-Line ('- Branch: ' + $Branch)
    Add-Line ('- HEAD: ' + $Head)
    Add-Line ('- Latest reachable tag: ' + $Tag)
    Add-Line ('- Working tree changes: ' + $Status.Count)

    Write-Utf8NoBom -Path (Join-Path $AuditDir 'git_status_short.txt') -Text ($Status -join "`r`n")
    Write-Utf8NoBom -Path (Join-Path $AuditDir 'git_recent_commits.txt') -Text ($Recent -join "`r`n")

    if ($Status.Count -gt 0) {
        Add-Finding -Severity 'MEDIUM' -Area 'git' -Message 'Working tree has uncommitted or untracked changes' -Evidence ($Status.Count.ToString() + ' entries')
    }
}
else {
    Add-Line '- Git available: no'
    Add-Finding -Severity 'MEDIUM' -Area 'git' -Message 'git.exe is not available; filesystem fallback used'
}

Add-Line ''
Add-Line '## Tool versions'
Invoke-AuditCommand -Name 'powershell_version' -Command '$PSVersionTable.PSVersion.ToString()' -WorkingDirectory $RootPath -TimeoutSeconds 30
Invoke-AuditCommand -Name 'git_version' -Command 'git --version' -WorkingDirectory $RootPath -TimeoutSeconds 30
Invoke-AuditCommand -Name 'python_version' -Command 'python --version' -WorkingDirectory $RootPath -TimeoutSeconds 30
Invoke-AuditCommand -Name 'node_version' -Command 'node --version' -WorkingDirectory $RootPath -TimeoutSeconds 30
Invoke-AuditCommand -Name 'npm_version' -Command 'npm --version' -WorkingDirectory $RootPath -TimeoutSeconds 30

Add-Line ''
Add-Line '## Required file coverage'
Add-Line ''
Add-Line '| File | Status | Note |'
Add-Line '|---|---:|---|'

$RequiredFiles = @(
    'README.md',
    'LAUNCH_CUSTOSOPS.bat',
    'STOP_CUSTOSOPS.bat',
    'scripts/launch-custosops.ps1',
    'scripts/run-backend.ps1',
    'scripts/run-frontend.ps1',
    'scripts/audit-platform-contract.ps1',
    'scripts/audit_platform_contract.py',
    'scripts/audit-evidence-module-contract.ps1',
    'scripts/check-ui-proof-artifact.ps1',
    'scripts/audit-custosops-local-repo.ps1',
    'backend/requirements.txt',
    'backend/app/main.py',
    'frontend/package.json',
    'frontend/src/App.tsx',
    'frontend/src/styles.css',
    'backend/app/schemas/risky_signin.py',
    'backend/app/analyzers/risky_signin_evidence.py',
    'backend/app/api/risky_signins.py',
    'backend/app/services/risky_signin_report.py',
    'backend/tests/test_risky_signin_evidence.py',
    'samples/risky_signins/sample-risky-signins.json',
    'docs/portfolio/CUSTOSOPS_SOC_POSITIONING.md',
    'docs/demo/CUSTOSOPS_DEMO_SCRIPT.md',
    'docs/demo/DEMO_WORKFLOW.md',
    'docs/onboarding/GETTING_STARTED.md',
    'docs/onboarding/FIRST_RUN_CHECKLIST.md',
    'docs/onboarding/TROUBLESHOOTING.md',
    'docs/launch/LAUNCHER_REFERENCE.md',
    'docs/roadmap/ROADMAP.md',
    'docs/roadmap/MILESTONE_32_RISKY_SIGNIN_EVIDENCE_REVIEW.md',
    'docs/architecture/PLATFORM_MODULE_CONTRACT.md',
    'docs/architecture/EVIDENCE_MODULE_HELPER_CONTRACT.md'
)
foreach ($File in $RequiredFiles) { Test-RequiredFile -RelativePath $File }

$RepoFiles = Get-RepoFiles -RepoRoot $RootPath
Write-Utf8NoBom -Path (Join-Path $AuditDir 'tracked_or_scanned_files.txt') -Text ($RepoFiles -join "`r`n")

Add-Line ''
Add-Line '## Generated artifact checks'
$ArtifactPatterns = [ordered]@{
    tracked_zip = '\.zip$'
    tracked_node_modules = '(^|/)node_modules/'
    tracked_venv = '(^|/)\.venv/'
    tracked_dist_or_build = '(^|/)(dist|build)/'
    tracked_proof_artifact = 'CUSTOSOPS_.*(SMOKE|AUDIT|PROOF).*'
}
foreach ($Name in $ArtifactPatterns.Keys) {
    $Matches = @($RepoFiles | Where-Object { $_ -match $ArtifactPatterns[$Name] })
    Add-Line ('- ' + $Name + ': ' + $Matches.Count)
    foreach ($Match in $Matches) {
        Add-Finding -Severity 'HIGH' -Area 'tracked-artifact' -Message ('Tracked file matched ' + $Name) -Evidence $Match
    }
}

Add-Line ''
Add-Line '## Public-safety scan'
$SafetyHits = @(Search-PublicSafetyHits -Files $RepoFiles)
if ($SafetyHits.Count -gt 0) {
    $SafetyJson = $SafetyHits | ConvertTo-Json -Depth 5
}
else {
    $SafetyJson = '[]'
}
Write-Utf8NoBom -Path (Join-Path $AuditDir 'public_safety_scan_hits.json') -Text $SafetyJson
$BlockingSafetyHits = @($SafetyHits | Where-Object { $_.blocks_publication })
Add-Line ('- Text scan hits: ' + $SafetyHits.Count)
Add-Line ('- Blocking scan hits: ' + $BlockingSafetyHits.Count)
Add-Line '- Details: public_safety_scan_hits.json'
Add-Line '- Review-only hits can include synthetic sample IPs, sample email addresses, and defensive security wording.'

Add-Line ''
Add-Line '## Validation commands'
if ($RunExistingContractAudits) {
    Invoke-AuditCommand -Name 'platform_contract_audit' -Command ('.\scripts\audit-platform-contract.ps1 -Root ' + [char]34 + $RootPath + [char]34) -WorkingDirectory $RootPath -TimeoutSeconds 300
    Invoke-AuditCommand -Name 'evidence_module_contract_audit' -Command ('.\scripts\audit-evidence-module-contract.ps1 -Root ' + [char]34 + $RootPath + [char]34 + ' -OutputDir ' + [char]34 + $OutputDir + [char]34) -WorkingDirectory $RootPath -TimeoutSeconds 300
}
else {
    Add-Line '- Existing contract audits skipped. Use -RunExistingContractAudits.'
}

if ($RunBackendTests) {
    $BackendDir = Join-Path $RootPath 'backend'
    $VenvPython = Join-Path $BackendDir '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $VenvPython) {
        Invoke-AuditCommand -Name 'backend_pytest' -Command '.\.venv\Scripts\python.exe -m pytest -q' -WorkingDirectory $BackendDir -TimeoutSeconds 300
    }
    else {
        Add-Line '- Backend tests skipped: backend\.venv\Scripts\python.exe not found.'
        Add-Finding -Severity 'MEDIUM' -Area 'validation' -Message 'Backend venv python not found' -Evidence $VenvPython
    }
}
else {
    Add-Line '- Backend tests skipped. Use -RunBackendTests.'
}

if ($RunFrontendBuild) {
    $FrontendDir = Join-Path $RootPath 'frontend'
    Invoke-AuditCommand -Name 'frontend_build' -Command 'npm.cmd run build' -WorkingDirectory $FrontendDir -TimeoutSeconds 300
}
else {
    Add-Line '- Frontend build skipped. Use -RunFrontendBuild.'
}

Add-Line ''
Add-Line '## SOC portfolio judgement'
Add-Line ''
Add-Line '| Area | Judgement |'
Add-Line '|---|---|'
Add-Line '| Defensive boundary | Strong. Keep local-first and read-only. |'
Add-Line '| Engineering proof | Strong if tests, build, contract audits, and UI proof pass. |'
Add-Line '| SOC job proof | Improved with risky sign-in evidence review; next proof should add demo notes and escalation package. |'
Add-Line '| Highest next ROI | Risky sign-in demo notes, escalation note, and then optional UI workspace. |'
Add-Line '| Public readiness | Do not publish until local audit, proof ZIP checker, and manual safety review are clean. |'

Add-Line ''
Add-Line '## Recommended next work'
Add-Line ''
Add-Line '1. Review public_safety_scan_hits.json for unexpected blocking entries.'
Add-Line '2. Keep generated audit/proof ZIPs outside the repo.'
Add-Line '3. Add the risky sign-in UI workspace only after the backend/API scenario remains stable.'
Add-Line '4. Re-run the Desktop UI proof before any public/demo milestone.'

if ($Findings.Count -gt 0) {
    $FindingsJson = $Findings | ConvertTo-Json -Depth 8
}
else {
    $FindingsJson = '[]'
}
Write-Utf8NoBom -Path (Join-Path $AuditDir 'findings.json') -Text $FindingsJson

if ($AuditOk) { Add-Line ''; Add-Line 'RESULT: OK' }
else { Add-Line ''; Add-Line 'RESULT: REVIEW REQUIRED' }

Write-Utf8NoBom -Path (Join-Path $AuditDir 'LOCAL_REPO_AUDIT.md') -Text ($Lines -join "`r`n")

if (Test-Path -LiteralPath $AuditZip) { Remove-Item -LiteralPath $AuditZip -Force }
Compress-Archive -Path (Join-Path $AuditDir '*') -DestinationPath $AuditZip -Force

Write-Host ''
Write-Host 'CustosOps local repo audit complete.' -ForegroundColor Green
Write-Host ('Audit folder: ' + $AuditDir)
Write-Host ('Audit ZIP:    ' + $AuditZip)
Write-Host ('Findings:     ' + $Findings.Count)
Write-Host ''

if ($AuditOk) { exit 0 }
exit 1
