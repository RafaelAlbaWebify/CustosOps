# Milestone 25 - Evidence Run History

## Goal

Add durable local evidence run tracking to CustosOps.

CustosOps can already collect/import evidence, analyze findings, generate reports, and archive outputs.

Run history adds the missing operational timeline.

## Slice 25A - Backend run history foundation

### Added

- Local run history JSON store.
- Evidence run schema.
- Backend service for recording, listing, and clearing runs.
- Backend API:
  - GET /api/runs
  - POST /api/runs
  - DELETE /api/runs
- Tests for create, list, clear, and limit behavior.

### Stored fields

Each run can track:

- run_id
- created_at
- module_id
- module_name
- source
- source_type
- asset
- status
- raw_count
- parsed_count
- finding_count
- severity counts
- warning count
- report IDs
- notes
- metadata

### Safety

The run history is local-only.

It does not upload evidence externally.

It does not change endpoint configuration.

It does not remediate findings.


## Slice 25B-1 - Run History Workspace UI

### Added

- Run History workspace in the frontend sidebar.
- GET /api/runs integration.
- DELETE /api/runs integration.
- Summary cards for run count, finding count, warnings, and failures.
- Run history table with timestamp, module, source, asset, status, counts, and run ID.

### Notes

Automatic workflow recording is intentionally left for the next slice.

This slice verifies that the frontend can display and manage backend run-history records safely.


## Slice 25B-1 UI Polish - Run History layout

The Run History workspace was visible and functional, but metric cards rendered as plain collapsed text because the frontend did not yet have the expected card/grid styling.

Added CSS for:

- metric-grid
- metric-card
- workspace-header
- actions
- panel
- data-table
- status-pill
- danger button state


## Slice 25B-2 - Automatic workflow recording

### Added

Successful evidence workflows now record local run-history metadata.

Covered workflows:

- Endpoint import
- Endpoint local collection
- DNS imports
- Application log import
- Windows Event import
- Windows Event local collection

### Behavior

Run recording is non-blocking.

If the run-history API is unavailable, the evidence workflow still completes and the browser console records a warning.

### Safety

Run history stores operational metadata only.

It does not upload evidence.

It does not perform remediation.
