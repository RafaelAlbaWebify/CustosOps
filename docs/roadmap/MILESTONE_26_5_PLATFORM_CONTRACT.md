# Milestone 26.5 - Platform Contract and UI Reliability Gate

## Goal

Stabilize CustosOps as a scalable platform before adding more evidence collectors.

The milestone exists because Redaction exposed a broader frontend lifecycle issue: some workspaces depended on manual Refresh or startup timing.

## Slice 26.5A - Platform Contract and Audit

### Added

- Platform module contract:
  - docs/architecture/PLATFORM_MODULE_CONTRACT.md
- Platform contract audit exporter:
  - scripts/audit-platform-contract.ps1
  - scripts/audit_platform_contract.py

### Validates

- Workspace type coverage.
- Navigation coverage.
- Render block coverage.
- Workspace lifecycle dispatcher coverage.
- Report redaction hooks.
- Run history and archive hooks.
- Zero-finding/evidence-readiness patterns.
- Frontend source growth risk.

### Output

The audit script creates a ZIP in the user's Downloads folder.

## Planned next slices

### 26.5B - API helper extraction

Move repeated fetch/request logic out of App.tsx.

### 26.5C - Workspace component extraction

Move Run History and Redaction workspaces into separate components first.

### 26.5D - Evidence module helper contract

Create reusable helper patterns for evidence modules before adding IIS/Application local collection.


### 26.5A Repair - App Log Workspace Contract

The initial platform audit expected the Application Logs workspace id as `app-logs`.

The actual frontend workspace id is `app-log`.

The audit and contract documentation now use the real frontend workspace id so the platform contract reflects the implemented app.


### 26.5A Repair - App Log Lifecycle Coverage

The `app-log` workspace now has explicit lifecycle dispatcher coverage.

Current behavior is intentionally import-driven until IIS/Application local collection is added.
