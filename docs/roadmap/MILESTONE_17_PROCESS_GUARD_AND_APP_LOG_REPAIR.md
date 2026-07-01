# Milestone 17 - Process Guard and App Log Repair

## Goal

Stabilize CustosOps local operation after adding Application Log Evidence.

## Fixed

- App Log report backend import error.
- Backend preflight now imports app.main before starting Uvicorn.
- Launcher waits for backend health before starting frontend.
- Stop/launch scripts target CustosOps ports only:
  - 8000 backend
  - 5173 frontend

## Added

- scripts/custosops-process-guard.ps1
- Port-aware stop behavior.
- Health-aware launch behavior.
- Clear backend/frontend startup messages.

## Safety

The stop command only targets listener processes on CustosOps ports 8000 and 5173.

It does not target unrelated Python or Node processes by name.

This avoids accidentally stopping unrelated local tools such as YTIS.