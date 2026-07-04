# CustosOps v0.28 Release Notes

## Current stable release

```text
custosops-v0.28.1-release-hygiene-readme-demo
```

## Release theme

v0.28 is the release-hardening line. The focus is audit alignment, README accuracy, demo readiness, and final product hygiene rather than new product modules.

## Major capabilities included

- 10-workspace frontend: Overview, Endpoint, DNS Hygiene, App Logs, Windows Events, IIS/Application, Reports, Archive, Run History, Redaction.
- Backend evidence modules for endpoint, DNS, app logs, Windows Events, and IIS/Application.
- Report builders and archive support.
- Evidence run history.
- Redaction controls and redaction-safe reports.
- Platform contract audit.
- Evidence module contract audit.
- Desktop UI proof gate with direct IIS/Application workspace coverage.

## Validation baseline

- Frontend build passes.
- Backend tests pass.
- Platform contract audit passes with 10 workspace rows.
- Evidence module contract audit passes including IIS/Application.
- Desktop UI proof passes with 10 workspaces.
- UI proof artifact checker requires IIS/Application proof artifacts.

## Release hygiene notes

- Placeholder-comment scan is clear after M28B.
- Basic secret-pattern scan may detect redaction test placeholders in `backend/app/services/app_log_redaction.py`.
- Those placeholders use `[REDACTED_*]` values and are expected examples, not live secrets.

## Finish-line guidance

After v0.28.1, avoid adding major features. The recommended next step is portfolio/demo packaging.
