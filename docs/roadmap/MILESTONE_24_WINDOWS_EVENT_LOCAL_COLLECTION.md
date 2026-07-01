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


# Milestone 24B - Windows Event Signal Quality

## Goal

Reduce noisy Windows Event findings after enabling real local collection.

## Added

- Provider-aware Windows Event analyzer logic.
- Service failure matching now requires Service Control Manager context.
- Winlogon 7001 events are not treated as service failures.
- Failed logon matching requires Security or Security-Auditing context.
- DNS Client matching requires DNS Client context.
- Reboot and update timeline matching uses provider/log context.
- Report wording now covers imported or locally collected evidence.
- Tests capture the false-positive pattern found during local TRON collection.

## Safety

This milestone changes classification logic only.

No remediation is performed.
No Windows Event logs are modified.
No endpoint configuration is changed.

# Milestone 24B UI Fix - Evidence-Based Report Readiness

## Problem

After a valid Windows Event local collection with zero matching events or zero findings, the report buttons stayed disabled until browser refresh.

## Fix

Windows Event report readiness is now based on loaded evidence, not finding count.

This allows operators to export a report for a valid collection even when no findings are detected.
