<#
.SYNOPSIS
    CustosOps Windows Event Evidence Collector v0.1

.DESCRIPTION
    Read-only local Windows Event evidence collector.

    It collects selected operational and security-relevant Windows Event records
    for CustosOps analysis.

    It does not clear logs.
    It does not modify services.
    It does not change endpoint configuration.
    It does not remediate findings.
    It does not collect credentials.
#>

[CmdletBinding()]
param(
    [string]$OutputPath = ".\windows-event-evidence.local.json",
    [int]$SinceHours = 72,
    [int]$MaxEventsPerLog = 300
)

Set-StrictMode -Version Latest

function ConvertTo-SafeString {
    param($Value)

    if ($null -eq $Value) {
        return ""
    }

    return [string]$Value
}

function ConvertTo-SafeEventRecord {
    param(
        [Parameter(Mandatory=$true)]
        $Event
    )

    $userValue = ""

    try {
        if ($null -ne $Event.UserId) {
            $userValue = ConvertTo-SafeString $Event.UserId.Value
        }
    }
    catch {
        $userValue = ""
    }

    $timestampValue = ""

    try {
        if ($null -ne $Event.TimeCreated) {
            $timestampValue = $Event.TimeCreated.ToString("o")
        }
    }
    catch {
        $timestampValue = ""
    }

    [ordered]@{
        record_number = $Event.RecordId
        timestamp     = $timestampValue
        provider      = ConvertTo-SafeString $Event.ProviderName
        event_id      = $Event.Id
        level         = ConvertTo-SafeString $Event.LevelDisplayName
        computer      = ConvertTo-SafeString $Event.MachineName
        log_name      = ConvertTo-SafeString $Event.LogName
        user          = $userValue
        message       = ConvertTo-SafeString $Event.Message
        raw           = [ordered]@{
            provider_name = ConvertTo-SafeString $Event.ProviderName
            id            = $Event.Id
            level         = $Event.Level
            level_display = ConvertTo-SafeString $Event.LevelDisplayName
            log_name      = ConvertTo-SafeString $Event.LogName
            record_id     = $Event.RecordId
        }
    }
}

$warnings = New-Object System.Collections.Generic.List[string]
$events = New-Object System.Collections.Generic.List[object]

$since = (Get-Date).AddHours(-1 * [Math]::Abs($SinceHours))

$logs = @(
    "Application",
    "System",
    "Security",
    "Microsoft-Windows-DNS-Client/Operational",
    "Microsoft-Windows-WindowsUpdateClient/Operational"
)

$eventIds = @(
    7000,
    7009,
    7011,
    7022,
    7023,
    7024,
    7026,
    7031,
    7034,
    7043,
    4625,
    1000,
    1001,
    1026,
    1014,
    1074,
    6005,
    6006,
    6008,
    19,
    20,
    21
)

foreach ($logName in $logs) {
    try {
        $filter = @{
            LogName   = $logName
            StartTime = $since
            Id        = $eventIds
        }

        $logEvents = Get-WinEvent -FilterHashtable $filter -MaxEvents $MaxEventsPerLog -ErrorAction Stop

        foreach ($event in $logEvents) {
            $events.Add((ConvertTo-SafeEventRecord -Event $event)) | Out-Null
        }
    }
    catch {
        $message = ConvertTo-SafeString $_.Exception.Message

        if ($message -notmatch "No events were found") {
            $warnings.Add(("Unable to read Windows Event log " + $logName + ": " + $message)) | Out-Null
        }
    }
}

$orderedEvents = @($events | Sort-Object {
    if ($_.timestamp) {
        $_.timestamp
    }
    else {
        ""
    }
})

$output = [ordered]@{
    source_file        = "local-windows-events"
    source_type        = "windows_event_log_local_collection"
    raw_event_count    = $orderedEvents.Count
    parsed_event_count = $orderedEvents.Count
    events             = $orderedEvents
    parser_warnings    = @($warnings)
}

$parent = Split-Path -Parent $OutputPath

if ($parent -and !(Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
}

$json = $output | ConvertTo-Json -Depth 12
Set-Content -LiteralPath $OutputPath -Value $json -Encoding UTF8

Write-Host ("CustosOps Windows Event evidence written to: " + $OutputPath)
Write-Host ("Events collected: " + $orderedEvents.Count)
Write-Host ("Warnings: " + $warnings.Count)
