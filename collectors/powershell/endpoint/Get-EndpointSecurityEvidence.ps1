<#
.SYNOPSIS
    CustosOps Endpoint Security Evidence Collector v0.1

.DESCRIPTION
    Read-only local Windows endpoint evidence collector.

    It collects security posture evidence useful for support, cyber hygiene,
    and remediation planning.

    It does not change endpoint configuration.
    It does not enable or disable services.
    It does not remediate findings.
    It does not collect credentials.
#>

[CmdletBinding()]
param(
    [string]$OutputPath = ".\endpoint-evidence.local.json"
)

Set-StrictMode -Version Latest

function ConvertTo-SafeString {
    param($Value)

    if ($null -eq $Value) {
        return ""
    }

    return [string]$Value
}

function Get-BestEffortValue {
    param(
        [Parameter(Mandatory=$true)]
        [scriptblock]$ScriptBlock,

        [object]$Fallback = "unknown"
    )

    try {
        return & $ScriptBlock
    }
    catch {
        return $Fallback
    }
}

function Get-PendingRebootEvidence {
    $checks = [ordered]@{
        ComponentBasedServicing = Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending"
        WindowsUpdate           = Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired"
        PendingFileRename       = $false
    }

    try {
        $sessionManager = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" -ErrorAction Stop
        if ($sessionManager.PendingFileRenameOperations) {
            $checks.PendingFileRename = $true
        }
    }
    catch {
        $checks.PendingFileRename = $false
    }

    [pscustomobject]@{
        IsPending = ($checks.ComponentBasedServicing -or $checks.WindowsUpdate -or $checks.PendingFileRename)
        Checks    = $checks
    }
}

function Get-SecureBootEvidence {
    Get-BestEffortValue -ScriptBlock {
        if (Confirm-SecureBootUEFI -ErrorAction Stop) {
            "enabled"
        }
        else {
            "disabled"
        }
    } -Fallback "unknown_or_unsupported"
}

function Get-TpmEvidence {
    Get-BestEffortValue -ScriptBlock {
        $tpm = Get-Tpm -ErrorAction Stop

        [pscustomobject]@{
            Present = [bool]$tpm.TpmPresent
            Ready   = [bool]$tpm.TpmReady
            Enabled = [bool]$tpm.TpmEnabled
            Owned   = [bool]$tpm.TpmOwned
        }
    } -Fallback ([pscustomobject]@{
        Present = $false
        Ready   = $false
        Enabled = $false
        Owned   = $false
        Status  = "unknown"
    })
}

function Get-BitLockerEvidence {
    Get-BestEffortValue -ScriptBlock {
        $volume = Get-BitLockerVolume -MountPoint $env:SystemDrive -ErrorAction Stop

        [pscustomobject]@{
            MountPoint       = ConvertTo-SafeString $volume.MountPoint
            ProtectionStatus = ConvertTo-SafeString $volume.ProtectionStatus
            VolumeStatus     = ConvertTo-SafeString $volume.VolumeStatus
            EncryptionMethod = ConvertTo-SafeString $volume.EncryptionMethod
        }
    } -Fallback ([pscustomobject]@{
        MountPoint       = $env:SystemDrive
        ProtectionStatus = "unknown"
        VolumeStatus     = "unknown"
        EncryptionMethod = "unknown"
    })
}

function Get-DefenderEvidence {
    Get-BestEffortValue -ScriptBlock {
        $status = Get-MpComputerStatus -ErrorAction Stop

        [pscustomobject]@{
            AntivirusEnabled       = [bool]$status.AntivirusEnabled
            RealTimeProtection     = [bool]$status.RealTimeProtectionEnabled
            BehaviorMonitorEnabled = [bool]$status.BehaviorMonitorEnabled
            IoavProtectionEnabled  = [bool]$status.IoavProtectionEnabled
            NISEnabled             = [bool]$status.NISEnabled
            AMServiceEnabled       = [bool]$status.AMServiceEnabled
            AntispywareEnabled     = [bool]$status.AntispywareEnabled
        }
    } -Fallback ([pscustomobject]@{
        Status = "unavailable"
    })
}

function Get-FirewallEvidence {
    Get-BestEffortValue -ScriptBlock {
        Get-NetFirewallProfile -ErrorAction Stop |
            Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction
    } -Fallback @()
}

function Get-LocalAdministratorsEvidence {
    Get-BestEffortValue -ScriptBlock {
        Get-LocalGroupMember -Group "Administrators" -ErrorAction Stop |
            Select-Object Name, ObjectClass, PrincipalSource
    } -Fallback @()
}

function Get-RdpEvidence {
    Get-BestEffortValue -ScriptBlock {
        $value = Get-ItemPropertyValue -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -ErrorAction Stop

        [pscustomobject]@{
            Enabled = ($value -eq 0)
            RegistryValue = $value
        }
    } -Fallback ([pscustomobject]@{
        Enabled = "unknown"
        RegistryValue = "unknown"
    })
}

function Get-Smbv1Evidence {
    Get-BestEffortValue -ScriptBlock {
        $cfg = Get-SmbServerConfiguration -ErrorAction Stop

        [pscustomobject]@{
            EnableSMB1Protocol = [bool]$cfg.EnableSMB1Protocol
        }
    } -Fallback ([pscustomobject]@{
        EnableSMB1Protocol = "unknown"
    })
}

function Get-ListeningPortsEvidence {
    Get-BestEffortValue -ScriptBlock {
        Get-NetTCPConnection -State Listen -ErrorAction Stop |
            Select-Object -First 80 LocalAddress, LocalPort, OwningProcess |
            ForEach-Object {
                $processName = "unknown"
                try {
                    $processName = (Get-Process -Id $_.OwningProcess -ErrorAction Stop).ProcessName
                }
                catch {
                    $processName = "unknown"
                }

                [pscustomobject]@{
                    LocalAddress = ConvertTo-SafeString $_.LocalAddress
                    LocalPort    = [int]$_.LocalPort
                    ProcessId    = [int]$_.OwningProcess
                    ProcessName  = $processName
                }
            }
    } -Fallback @()
}

function Get-InstalledSoftwareEvidence {
    $paths = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )

    $items = New-Object System.Collections.Generic.List[object]

    foreach ($path in $paths) {
        try {
            Get-ItemProperty -Path $path -ErrorAction Stop |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_.DisplayName) } |
                ForEach-Object {
                    $items.Add([pscustomobject]@{
                        DisplayName    = ConvertTo-SafeString $_.DisplayName
                        DisplayVersion = ConvertTo-SafeString $_.DisplayVersion
                        Publisher      = ConvertTo-SafeString $_.Publisher
                        InstallDate    = ConvertTo-SafeString $_.InstallDate
                    }) | Out-Null
                }
        }
        catch {
            # Best effort only.
        }
    }

    $items |
        Sort-Object DisplayName, DisplayVersion -Unique |
        Select-Object -First 300
}

function Write-JsonNoBom {
    param(
        [Parameter(Mandatory=$true)]$Object,
        [Parameter(Mandatory=$true)][string]$Path
    )

    $resolved = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($Path)
    $parent = Split-Path -Parent $resolved

    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    $json = $Object | ConvertTo-Json -Depth 10
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($resolved, $json, $utf8NoBom)

    return $resolved
}

$os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
$computerSystem = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop
$bios = Get-CimInstance Win32_BIOS -ErrorAction Stop
$product = Get-CimInstance Win32_ComputerSystemProduct -ErrorAction Stop

$evidence = [ordered]@{
    schema_version = "custosops.endpoint.v0.1"
    collected_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    collector = "Get-EndpointSecurityEvidence.ps1"
    collector_mode = "read_only"
    computer = [ordered]@{
        computer_name = $env:COMPUTERNAME
        current_user = $env:USERNAME
        manufacturer = ConvertTo-SafeString $computerSystem.Manufacturer
        model = ConvertTo-SafeString $computerSystem.Model
        serial_number = ConvertTo-SafeString $product.IdentifyingNumber
        domain = ConvertTo-SafeString $computerSystem.Domain
    }
    operating_system = [ordered]@{
        caption = ConvertTo-SafeString $os.Caption
        version = ConvertTo-SafeString $os.Version
        build_number = ConvertTo-SafeString $os.BuildNumber
        install_date = ConvertTo-SafeString $os.InstallDate
        last_boot_time = ConvertTo-SafeString $os.LastBootUpTime
    }
    firmware = [ordered]@{
        bios_version = ConvertTo-SafeString $bios.SMBIOSBIOSVersion
        bios_date = ConvertTo-SafeString $bios.ReleaseDate
        secure_boot = Get-SecureBootEvidence
        tpm = Get-TpmEvidence
    }
    encryption = [ordered]@{
        bitlocker = Get-BitLockerEvidence
    }
    protection = [ordered]@{
        defender = Get-DefenderEvidence
        firewall_profiles = @(Get-FirewallEvidence)
    }
    access_surface = [ordered]@{
        local_administrators = @(Get-LocalAdministratorsEvidence)
        rdp = Get-RdpEvidence
        smbv1 = Get-Smbv1Evidence
        listening_ports = @(Get-ListeningPortsEvidence)
    }
    maintenance = [ordered]@{
        pending_reboot = Get-PendingRebootEvidence
    }
    software = [ordered]@{
        installed_software = @(Get-InstalledSoftwareEvidence)
    }
    safety = [ordered]@{
        changed_configuration = $false
        collected_credentials = $false
        remediation_performed = $false
    }
}

$writtenPath = Write-JsonNoBom -Object $evidence -Path $OutputPath

Write-Host "CustosOps endpoint evidence written to:"
Write-Host $writtenPath