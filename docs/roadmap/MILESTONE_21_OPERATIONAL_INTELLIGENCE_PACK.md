# Milestone 21 - Operational Intelligence Pack v0.1

## Slice 21A - Finding Review Workflow

### Added

- Local finding review status.
- Operator notes per finding.
- Review timestamp.
- Reviewed-by metadata.
- Browser-local persistence for review decisions.
- Report export includes review metadata.

### Review statuses

- Open
- Reviewed
- Needs follow-up
- Accepted risk
- False positive

### Safety

This workflow does not remediate findings.

Review metadata is stored locally in browser storage and included only when the operator generates reports.


## Slice 21B - Evidence Redaction and API Error Summary

### Added

- Pattern-based redaction helper for common secret/token formats.
- App Log report exports redact obvious sensitive values.
- App Log import now calculates API operational summary metadata.
- App Log reports include:
  - HTTP request count
  - failed request count
  - server error count
  - authentication failure count
  - status-code breakdown
  - top failing endpoints
  - top client IPs
  - slowest requests
  - first seen and last seen timestamps

### Safety

Redaction is pattern-based and should reduce accidental disclosure in exported reports.

Raw evidence remains local. Redaction should not be treated as a guarantee that every possible secret format has been removed.


## Slice 21C - Windows Event Log Evidence v0.1

### Added

- Windows Event JSON/CSV import backend.
- Synthetic Windows Event sample evidence.
- Detection for:
  - service failures
  - failed logons
  - application errors
  - DNS client resolution events
  - reboot, shutdown, and update timeline signals
- HTML, Markdown, and JSON report generation.
- Archive-compatible report route.

### Safety

This slice uses imported evidence only.

No Windows Event logs are collected live and no host changes are made.


## Slice 21C UI - Windows Event Workspace

### Added

- Windows Events workspace in the frontend sidebar.
- Sample Windows Event findings are loaded from the backend.
- Windows Event JSON/CSV import from the browser UI.
- Windows Event findings use the standard Evidence Review workspace.
- Windows Event reports can be generated from the Reports workspace.

### Safety

The frontend imports user-selected JSON/CSV evidence only.

No live Windows Event collection is performed in this slice.


## Slice 21D - Executive Summary Pack v0.1

### Added

- Backend executive summary report engine.
- Combined report input for Endpoint, DNS, App Log, and Windows Event modules.
- Portfolio-level severity counts.
- Portfolio-level review status counts.
- Module summaries.
- Top risks.
- Recommended next actions.
- HTML, Markdown, and JSON export formats.
- Archive-compatible report route.

### Safety

The executive summary pack only summarizes evidence already loaded into CustosOps.

No remediation is performed and no evidence is uploaded externally.
