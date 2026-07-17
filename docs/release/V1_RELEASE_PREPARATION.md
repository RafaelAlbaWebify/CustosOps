# CustosOps v1.0 Release Preparation

This document is the controlled draft for the first portfolio-ready CustosOps release. Do not publish the release until Issue #34 is completed with fresh Windows acceptance evidence.

## Proposed Release

- Tag: `v1.0.0`
- Title: `CustosOps v1.0.0 — Local-First Defensive Evidence Console`
- Target branch: `master`
- Final commit: record only after clean-machine acceptance passes

## Draft Release Notes

CustosOps v1.0.0 is the first portfolio-ready release of a local-first, read-only defensive security evidence and reporting console for Windows and Microsoft-oriented support environments.

### Included

- Ten UI workspaces: Overview, Endpoint, DNS Hygiene, App Logs, Windows Events, IIS/Application, Reports, Archive, Run History, and Redaction.
- Read-only local collection and JSON import workflows.
- Finding classification with severity, confidence, limitations, and safe next steps.
- HTML, Markdown, and JSON report generation.
- Report archive and evidence run history.
- Redaction preview and report-redaction controls.
- Endpoint, DNS/email-domain, application-log, Windows Event, and IIS/application evidence scenarios.
- Synthetic Microsoft 365 / Entra-style risky-sign-in evidence review through the backend/API scenario.
- Windows launch and stop workflows.
- Full local repository audit and Desktop UI proof workflows.
- Linux and Windows continuous verification.
- Browser-based workspace and SOC workflow checks.
- Dependency security audit and CycloneDX inventory generation.

### Technology Baseline

- React 19.2.7
- React DOM 19.2.7
- TypeScript 7.0.2
- Vite 8
- FastAPI backend
- PowerShell 5.1-compatible Windows automation

### Product Boundary

CustosOps is not a SIEM, EDR, vulnerability scanner, MDR/MSSP platform, penetration-testing tool, exploit framework, auto-remediation platform, or live tenant-monitoring service.

It does not unlock accounts, reset credentials, change DNS or IP settings, remediate endpoints, or perform tenant-wide scans. Demonstrations and committed fixtures use synthetic or local sample evidence only.

### Requirements

- Windows 10 or Windows 11
- PowerShell 5.1 or newer
- Python 3.11 or newer on `PATH`
- Node.js LTS with npm on `PATH`
- Git when cloning the repository

No Docker, cloud account, production credential, or production environment is required.

### First Run

From the repository root:

```powershell
.\LAUNCH_CUSTOSOPS.bat
```

Stop the application with:

```powershell
.\STOP_CUSTOSOPS.bat
```

Run full local validation with:

```powershell
.\AUDIT_CUSTOSOPS_FULL.bat
```

Run final clean-machine acceptance with:

```powershell
.\ACCEPT_CUSTOSOPS_V1.bat
```

### Known Limitations

- The risky-sign-in scenario is synthetic and backend/API first; it is not live tenant monitoring.
- The platform is local-first and evidence-focused rather than a real-time detection system.
- The Desktop UI proof requires the companion `CustosOps-UI-Tool` on Windows.
- Findings support review and escalation; they do not perform remediation.

## Final Publication Checklist

### Repository state

- [ ] Issue #34 is closed with a passing clean-machine acceptance ZIP.
- [ ] Evidence ZIP names and SHA-256 hashes are recorded.
- [ ] `master` matches the exact accepted commit.
- [ ] All required GitHub Actions workflows are green on that commit.
- [ ] No release-blocking pull request or issue remains open.

### Public-safety review

- [ ] README renders correctly and matches the release scope.
- [ ] Screenshots, reports, console logs, network logs, and paths are manually reviewed.
- [ ] No credentials, workplace names, customer names, or private local paths are present.
- [ ] No generated ZIP or local proof artifact is tracked in Git.
- [ ] Synthetic/local-evidence wording is visible in README and release notes.

### Release metadata

- [ ] Replace the final-commit placeholder with the accepted SHA.
- [ ] Confirm repository description and topics.
- [ ] Confirm the social preview is suitable for portfolio review.
- [ ] Create annotated tag `v1.0.0` on the accepted commit.
- [ ] Publish the GitHub release using the reviewed notes above.
- [ ] Verify the tag and release both point to the accepted commit.
- [ ] Verify the first-time evaluator path from README through launch and demo guidance.

## Evidence Record Template

```text
Accepted commit:
Acceptance ZIP:
Acceptance ZIP SHA-256:
Local audit ZIP:
Local audit ZIP SHA-256:
UI proof ZIP:
UI proof ZIP SHA-256:
Acceptance date:
Windows version:
PowerShell version:
Python version:
Node/npm version:
Reviewer:
```
