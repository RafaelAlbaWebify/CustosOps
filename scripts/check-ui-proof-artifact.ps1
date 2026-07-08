param(
    [string]$ZipPath,
    [string]$Downloads,
    [string]$StatusFile
)

$ProofOk = $true

function Add-Fail {
    param([string]$Message)
    Write-Host "FAILED: $Message" -ForegroundColor Red
    $script:ProofOk = $false
}

function Get-ZipEntryText {
    param(
        [object]$Zip,
        [string]$EntryName
    )

    $Entry = $Zip.Entries | Where-Object { $_.FullName.Replace("\","/") -eq $EntryName } | Select-Object -First 1
    if (-not $Entry) {
        Add-Fail "Missing ZIP entry: $EntryName"
        return ""
    }

    $Stream = $Entry.Open()
    $Reader = New-Object System.IO.StreamReader($Stream)
    try {
        return $Reader.ReadToEnd()
    }
    finally {
        $Reader.Close()
        $Stream.Close()
    }
}

if (-not $Downloads) {
    $Downloads = Join-Path $env:USERPROFILE "Downloads"
}

if (-not $ZipPath) {
    $Latest = Get-ChildItem -LiteralPath $Downloads -Filter "CUSTOSOPS_UI_SMOKE_*.zip" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($Latest) {
        $ZipPath = $Latest.FullName
    }
}

Write-Host "CustosOps UI proof artifact checker"
Write-Host "ZIP: $ZipPath"

if (-not $ZipPath) {
    Add-Fail "No CUSTOSOPS_UI_SMOKE ZIP found"
}
elseif (-not (Test-Path -LiteralPath $ZipPath)) {
    Add-Fail "ZIP does not exist: $ZipPath"
}

if ($ProofOk) {
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $Zip = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)

        try {
            $SummaryText = Get-ZipEntryText -Zip $Zip -EntryName "00-ui-smoke-summary.json"
            $ChecksText = Get-ZipEntryText -Zip $Zip -EntryName "logs/ui-checks.json"
            $StartupText = Get-ZipEntryText -Zip $Zip -EntryName "startup-status.txt"

            if ($SummaryText) {
                $Summary = $SummaryText | ConvertFrom-Json

                if (-not $Summary.checksOk) { Add-Fail "summary checksOk is not true" }
                if ([int]$Summary.consoleErrorCount -ne 0) { Add-Fail "consoleErrorCount is not zero" }
                if ([int]$Summary.pageErrorCount -ne 0) { Add-Fail "pageErrorCount is not zero" }
                if ([int]$Summary.failedRequestCount -ne 0) { Add-Fail "failedRequestCount is not zero" }
                if ([int]$Summary.workspaceCount -lt 10) { Add-Fail "workspaceCount is less than 10" }
            }

            if ($StartupText) {
                if ($StartupText -notlike "*Backend ready: True*") { Add-Fail "Backend ready marker missing" }
                if ($StartupText -notlike "*Frontend ready: True*") { Add-Fail "Frontend ready marker missing" }
            }

            if ($ChecksText) {
                $Checks = $ChecksText | ConvertFrom-Json

                $RequiredIds = @(
                    "overview",
                    "endpoint",
                    "dns",
                    "app-log",
                    "windows-events",
                    "iis",
                    "reports",
                    "archive",
                    "run-history",
                    "redaction"
                )

                foreach ($RequiredId in $RequiredIds) {
                    $Match = $Checks | Where-Object { $_.id -eq $RequiredId -and $_.ok -eq $true } | Select-Object -First 1
                    if (-not $Match) {
                        Add-Fail "Missing passing UI check: $RequiredId"
                    }
                }

                $IisScreenshot = $Zip.Entries | Where-Object { $_.FullName.Replace("\","/") -eq "screenshots/iis-iis-application.png" } | Select-Object -First 1
                if (-not $IisScreenshot) {
                    Add-Fail "Missing IIS workspace screenshot"
                }

                $ExpectedRedaction = "Contact [REDACTED_EMAIL] from C:\Users\[REDACTED_USER]\Desktop"
                $RedactionPreview = $Checks | Where-Object { $_.action -eq "redaction-preview" } | Select-Object -First 1

                if (-not $RedactionPreview) {
                    Add-Fail "Missing redaction-preview action"
                }
                else {
                    if (-not $RedactionPreview.redactedMarkersFound) { Add-Fail "redaction-preview markers not found" }
                    if ($RedactionPreview.outputValue -ne $ExpectedRedaction) { Add-Fail "redaction-preview output mismatch" }
                }

                $FailedChecks = $Checks | Where-Object { $_.ok -ne $true }
                if ($FailedChecks) { Add-Fail "One or more UI checks are not ok" }
            }
        }
        finally {
            $Zip.Dispose()
        }
    }
    catch {
        Add-Fail $_.Exception.Message
    }
}

if ($StatusFile) {
    if ($ProofOk) {
        Set-Content -LiteralPath $StatusFile -Value "OK" -Encoding ASCII
    }
    else {
        Set-Content -LiteralPath $StatusFile -Value "FAILED" -Encoding ASCII
    }
}

if ($ProofOk) {
    Write-Host "UI proof artifact check: OK" -ForegroundColor Green
    exit 0
}

Write-Host "UI proof artifact check: FAILED" -ForegroundColor Red
exit 1
