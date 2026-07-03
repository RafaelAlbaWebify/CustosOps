# M27A - IIS/Application Backend Evidence Core

Status: complete

Purpose:

Add the backend evidence core for read-only IIS/Application local collection before adding frontend workspace integration.

Scope:

```text
In scope:
- IIS/Application evidence schema.
- IIS/Application import API.
- IIS/Application read-only local collector API.
- IIS/Application analyzer.
- IIS/Application report builder.
- IIS/Application report API route.
- Backend tests for zero-IIS state, findings, report generation, and local collection response shape.
- Evidence contract audit update.

Out of scope:
- Frontend IIS workspace.
- Remediation actions.
- Service restart/start/stop actions.
- Admin-only requirements.
- IIS configuration changes.
```

Important behavior:

```text
No IIS installed, no appcmd.exe, or no IIS logs is a valid evidence state.
The collector reports what is available and does not fail merely because IIS is absent.
```

Validation:

```text
1. frontend build
2. backend pytest
3. platform contract audit
4. evidence module contract audit
5. Desktop UI proof smoke
6. UI proof artifact checker
```

Release tag:

```text
custosops-v0.27.0-iis-application-evidence-backend
```

Next recommended milestone:

```text
M27B - IIS/Application frontend workspace and run-history integration
```
