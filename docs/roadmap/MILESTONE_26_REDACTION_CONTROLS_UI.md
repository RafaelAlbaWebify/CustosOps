# Milestone 26 - Redaction Controls UI

## Goal

Give operators visible control over what CustosOps redacts in evidence previews and reports.

CustosOps already uses local evidence and avoids remediation.

This milestone makes redaction behavior explicit and configurable.

## Slice 26A - Redaction settings backend

### Added

- Local redaction settings schema.
- Local JSON settings store.
- Backend redaction settings service.
- API routes:
  - GET /api/redaction/settings
  - PUT /api/redaction/settings
  - POST /api/redaction/settings/reset
- Tests for default, update, reset, persistence, and invalid rule validation.

### Default rules

- Email addresses: enabled.
- Windows user profile paths: enabled.
- IPv4 addresses: disabled by default because they are often operationally useful.
- Hostnames: disabled by default because asset identity is normally required for evidence review.

### Safety

The settings are local-only.

No evidence is uploaded.

No remediation is performed.

Slice 26A does not yet apply these settings to reports. It creates the durable settings foundation first.


## Slice 26B - Redaction Controls UI

### Added

- Redaction Settings workspace in the frontend sidebar.
- GET /api/redaction/settings integration.
- PUT /api/redaction/settings integration.
- POST /api/redaction/settings/reset integration.
- Profile name editing.
- Global redaction enabled toggle.
- Rule enabled toggles.
- Replacement text editing.
- Summary cards for profile, global state, enabled rules, and total rules.

### Notes

This slice exposes and saves local redaction settings.

Applying the settings to report generation is intentionally left for Slice 26C.
