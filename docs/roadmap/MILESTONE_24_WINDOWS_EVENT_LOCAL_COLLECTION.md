# Milestone 24A - Windows Event Local Collection

## Goal

Turn the Windows Event Evidence module from sample/import-only into a practical local evidence collection workflow.

## Added

- Read-only PowerShell Windows Event collector.
- Backend local collection service.
- Backend route: POST /api/windows-events/collect-local.
- Frontend Collect Local button in the Windows Event workspace.
- Tests for the local collection route and read-only collector script.

## Evidence collected

The collector targets operationally useful event families:

- Service failures.
- Failed logons.
- Application errors.
- DNS client errors.
- Reboot, shutdown, and update timeline signals.

## Safety

The collector is read-only.

It does not clear logs.
It does not modify services.
It does not change endpoint configuration.
It does not remediate findings.
It does not collect credentials.
It does not upload evidence externally.

## Limitations

Some logs, especially Security, may require elevated permissions.

If a log cannot be read, the collector records a warning and continues with the other logs.
