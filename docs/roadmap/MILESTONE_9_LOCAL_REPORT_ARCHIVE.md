# Milestone 9 - Local Report Archive v0.1

## Goal

Keep a local archive of generated CustosOps reports.

Before this milestone, reports were downloaded by the browser only.

After this milestone, generated endpoint and DNS reports are also stored locally under:

reports/custosops_archive

## Added

- Local report archive service
- Archive manifest
- Endpoint report archiving
- DNS report archiving
- Archive listing API
- Frontend archive section

## New API Endpoint

GET /api/reports/archive

## Storage

Generated reports are stored under:

reports/custosops_archive/<report_type>/<YYYYMMDD>/

The archive manifest is stored at:

reports/custosops_archive/manifest.json

## Safety

The archive is local only.

CustosOps does not upload reports to cloud storage.

## Limitations

- No delete/archive cleanup UI yet.
- No report open button from the frontend yet.
- No PDF export yet.
- No customer/project tagging yet.