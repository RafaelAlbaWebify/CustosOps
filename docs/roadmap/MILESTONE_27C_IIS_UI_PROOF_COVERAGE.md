# M27C - IIS UI Proof Coverage

Status: complete

Purpose:

Update the local Desktop UI proof gate so the IIS/Application workspace added in M27B is directly validated.

Scope:

```text
In scope:
- Repair and update the Desktop Playwright UI proof script.
- Add direct #iis workspace capture.
- Require 10 passing workspaces in the proof artifact checker.
- Require an IIS workspace screenshot in the proof ZIP.
- Keep product runtime code unchanged.

Out of scope:
- New product features.
- Backend evidence changes.
- Frontend runtime changes.
- Remediation behavior.
```

Validation:

```text
1. frontend build
2. backend pytest
3. Desktop UI proof smoke
4. UI proof artifact checker
```

Release tag:

```text
custosops-v0.27.2-iis-ui-proof-coverage
```

Next recommended milestone:

```text
M28 - Release hardening and final polish
```
