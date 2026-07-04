# M27B - IIS/Application Frontend Workspace and Run History

Status: complete

Purpose:

Expose the M27A IIS/Application backend evidence core in the CustosOps frontend workspace lifecycle.

Scope:

```text
In scope:
- Add IIS/Application workspace navigation.
- Add sample loading, JSON import, and read-only local collection actions.
- Add IIS/Application report buttons and report center card.
- Persist IIS/Application evidence in local session state.
- Record IIS/Application import and local collection in run history.
- Add IIS/Application overview card and readiness indicators.

Out of scope:
- RedactionSettingsWorkspace extraction.
- Backend IIS collector redesign.
- Remediation actions.
- IIS service/app pool start/stop/restart.
```

Important behavior:

```text
No IIS installed remains a valid collection state.
No appcmd.exe remains a warning, not a failure.
No IIS log folder remains a warning, not a failure.
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
custosops-v0.27.1-iis-application-frontend-workspace
```

Next recommended milestone:

```text
M28 - Release hardening and product finish pass
```
