# CustosOps

CustosOps is a local-first cybersecurity evidence, posture, and reporting platform for Windows and Microsoft-oriented support environments.

It collects or imports read-only operational evidence, classifies findings with confidence and limitations, and generates support-ready reports that can be reviewed, archived, redacted, and traced through run history.

## Current v0.28 workspace map

CustosOps currently exposes 10 UI workspaces:

1. Overview
2. Endpoint
3. DNS Hygiene
4. App Logs
5. Windows Events
6. IIS/Application
7. Reports
8. Archive
9. Run History
10. Redaction

## Evidence modules

- Endpoint security evidence
- DNS hygiene evidence
- Application log evidence
- Windows Event evidence
- IIS/Application evidence

## Core platform capabilities

- Read-only local collection and JSON import workflows
- Finding classification with severity, confidence, limitations, and safe next steps
- HTML, Markdown, and JSON report generation
- Report archive
- Evidence run history
- Redaction preview and report redaction controls
- Desktop UI proof artifacts with screenshots, HTML captures, network logs, console logs, and workspace checks

## Positioning

CustosOps is not a penetration-testing tool, exploit framework, SIEM, EDR, vulnerability scanner, cloud collector, or auto-remediation platform.

It is designed to demonstrate and support practical cybersecurity and application-support evidence workflows:

- evidence before conclusion
- safe read-only troubleshooting
- support-ready reporting
- local audit proof
- portfolio-ready demonstration of engineering discipline

## Safety boundaries

- Local-first by default
- Read-only collection unless explicitly changed in a future version
- No exploitation
- No credential storage
- No automatic remediation
- No customer, employer, or production-sensitive data in demos
- Findings must include limitations and safe next steps

## Quick start

Start the local application:

```powershell
.\LAUNCH_CUSTOSOPS.bat
```

Stop the local application:

```powershell
.\STOP_CUSTOSOPS.bat
```

Run backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Run frontend build:

```powershell
cd frontend
npm.cmd run build
```

Run platform contract audit:

```powershell
.\scripts\audit-platform-contract.ps1 -Root .
```

Run evidence module contract audit:

```powershell
.\scripts\audit-evidence-module-contract.ps1 -Root . -OutputDir "$env:USERPROFILE\Downloads"
```

Run Desktop UI proof from the companion UI proof tool:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Desktop\CustosOps-UI-Tool\Run-CustosOps-UI-Smoke.ps1"
```

Validate a UI proof ZIP:

```powershell
.\scripts\check-ui-proof-artifact.ps1 -ZipPath "$env:USERPROFILE\Downloads\CUSTOSOPS_UI_SMOKE_<timestamp>.zip"
```

## Demo guidance

Use synthetic or local sample evidence only. A good demo should show:

1. Open Overview and explain the local-first positioning.
2. Import or collect one evidence module.
3. Review findings and limitations.
4. Generate a report.
5. Show the Archive and Run History.
6. Show Redaction controls.
7. Run or show the Desktop UI proof ZIP with 10 checked workspaces.

More detailed demo guidance is available in `docs/demo/CUSTOSOPS_DEMO_SCRIPT.md`.

## Release status

Current stable baseline:

```text
custosops-v0.28.1-release-hygiene-readme-demo
```

The v0.28 line is intended as the final hardening line before portfolio/demo packaging.
