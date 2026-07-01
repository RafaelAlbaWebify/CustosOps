# Milestone 12 - Local Report Archive Actions v0.1

## Goal

Make the local report archive actionable from the CustosOps UI.

## Added

- Open archived report
- Download archived report
- Delete archived report
- Backend archive entry safety checks
- Manifest cleanup for missing files

## New API Endpoints

- GET /api/reports/archive/{entry_id}/open
- GET /api/reports/archive/{entry_id}/download
- DELETE /api/reports/archive/{entry_id}

## Safety

Archive paths are resolved through the manifest and validated to remain under:

reports/custosops_archive

The UI actions only affect locally generated CustosOps report files.