# M31C - Local Repository Audit

Status: in progress until validated with a local audit ZIP.

Purpose:

Create a first-class read-only audit workflow for the local CustosOps working folder before public/demo review.

Why this matters:

```text
GitHub shows committed repository state.
The local folder can still contain uncommitted changes, generated ZIPs, proof artifacts, dependency folders, private references, stale tags, or validation drift.
```

Scope:

```text
- add scripts/audit-custosops-local-repo.ps1
- document the audit in README validation commands
- write audit output to Downloads as CUSTOSOPS_LOCAL_REPO_AUDIT_<timestamp>.zip
- capture Git state and recent commits
- check required project files
- check tracked generated artifacts and dependency folders
- scan public-safety keyword risks
- optionally run existing contract audits
- optionally run backend tests and frontend build
```

Safety boundary:

```text
The audit is read-only.
It does not modify source files.
It does not collect credentials.
It does not inspect external systems.
It does not perform offensive security testing.
```

Validation command:

```powershell
.\scripts\audit-custosops-local-repo.ps1 -Root . -RunExistingContractAudits -RunBackendTests -RunFrontendBuild
```

Expected output:

```text
%USERPROFILE%\Downloads\CUSTOSOPS_LOCAL_REPO_AUDIT_<timestamp>.zip
```

Completion criteria:

```text
- audit ZIP generated successfully
- findings.json reviewed
- public_safety_scan_hits.json reviewed for false positives and true risks
- backend tests pass or failures are explained
- frontend build passes or failures are explained
- contract audits pass or failures are explained
- no generated ZIP/proof artifacts are tracked
- no workplace/customer/private references remain in public-facing files
```

Next recommended milestone:

```text
M32 - Risky Sign-In Evidence Review
```

M32 should add a SOC-relevant, read-only, public-safe scenario using synthetic Microsoft 365 / Entra-style sign-in evidence.
