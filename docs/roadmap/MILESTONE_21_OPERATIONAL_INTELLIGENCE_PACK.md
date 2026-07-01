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
