# M32B - Full Proof Launcher

## Status

Complete.

## Purpose

Reduce manual validation steps before a CustosOps demo, release tag, or public-review checkpoint.

## What changed

```text
- Added PROVE_CUSTOSOPS_FULL.bat at the repository root.
- Added scripts/prove-custosops-full.ps1.
- Kept AUDIT_CUSTOSOPS_FULL.bat as the faster repo-only audit path.
- Documented the difference between repo audit and full proof in README.md.
```

## Validation flow

The full proof launcher runs:

```text
1. Full local repository audit.
2. Platform contract audit.
3. Evidence module contract audit.
4. Backend tests.
5. Frontend build.
6. External Desktop UI proof tool.
7. UI proof artifact checker.
```

## Expected external UI proof tool path

```text
%USERPROFILE%\Desktop\CustosOps-UI-Tool\Run-CustosOps-UI-Smoke.ps1
```

## Why this matters

The repository audit proves code, tests, contract checks, and local safety checks.

The Desktop UI proof proves the actual browser experience still loads, renders, and captures the expected 10 workspaces.

Before this milestone, those two proof paths had to be remembered and run separately. M32B gives the project one clear command for demo/public-readiness validation.

## Commands

Repo-only audit:

```powershell
.\AUDIT_CUSTOSOPS_FULL.bat
```

Full proof:

```powershell
.\PROVE_CUSTOSOPS_FULL.bat
```

Advanced full proof command:

```powershell
.\scripts\prove-custosops-full.ps1 -Root . -RequireUiProof
```

## Safety boundary

The proof launcher does not modify source files, production systems, identity systems, endpoints, firewall rules, DNS records, or external services.
