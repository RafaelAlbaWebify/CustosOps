# CustosOps

> My SOC / defensive security operations flagship.

CustosOps is a local-first cybersecurity evidence, posture and reporting platform for Windows and Microsoft-oriented support environments.

I am building it as my **SOC flagship**: a read-only defensive evidence console for SMB security hygiene reviews, local evidence analysis, finding classification, report generation and escalation-ready documentation.

## Flagship Area

| Area | Flagship | Target role |
|---|---|---|
| SOC - Security Operations | CustosOps | SOC Analyst |

## Current Stable Baseline

```text
custosops-v0.31.0-beginner-runbook-launch-audit
```

## Who This Is For

CustosOps is designed for:

```text
- IT support engineers
- application support engineers
- security operations learners
- SMB security hygiene reviews
- portfolio demonstrations
```

## What CustosOps Is Not

CustosOps is not:

```text
- a SIEM
- an EDR
- a vulnerability scanner
- an MDR/MSSP platform
- a penetration-testing tool
- an exploit framework
- an auto-remediation platform
```

It is a read-only defensive evidence console.

## Workspaces

CustosOps exposes 10 UI workspaces:

```text
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
```

## Evidence Modules

```text
- Endpoint security evidence
- DNS hygiene evidence
- Application log evidence
- Windows Event evidence
- IIS/Application evidence
```

## Core Capabilities

```text
- Read-only local collection and JSON import workflows
- Finding classification with severity, confidence, limitations, and safe next steps
- HTML, Markdown, and JSON report generation
- Report archive
- Evidence run history
- Redaction preview and report redaction controls
- Desktop UI proof artifacts with screenshots, HTML captures, network logs, console logs, and workspace checks
```

## Requirements

Recommended for a first run:

```text
- Windows 10 or Windows 11
- PowerShell 5.1 or newer
- Python 3.11 or newer on PATH
- Node.js LTS with npm on PATH
- Git, if cloning from GitHub
```

No Docker, cloud account, credentials, or production environment is required.

## Quick Start For Non-Expert Users

From the repository root, run:

```powershell
.\LAUNCH_CUSTOSOPS.bat
```

On first run, the launcher will:

```text
1. Check and clear stale CustosOps listeners on ports 8000 and 5173.
2. Start the backend in its own PowerShell window.
3. Create the backend Python virtual environment if missing.
4. Install backend dependencies if needed.
5. Wait for backend health at http://127.0.0.1:8000/api/health.
6. Start the frontend in its own PowerShell window.
7. Install frontend npm dependencies if needed.
8. Wait for frontend port 5173.
9. Open the browser at http://localhost:5173.
```

Keep the backend and frontend PowerShell windows open while using the app.

## Stop The App

From the repository root, run:

```powershell
.\STOP_CUSTOSOPS.bat
```

This stops CustosOps processes listening on ports 8000 and 5173.

## Important Port Note

CustosOps uses:

```text
Backend:  http://127.0.0.1:8000
Frontend: http://localhost:5173
```

The launcher is designed to stop stale CustosOps processes on those ports. If another non-CustosOps app is using one of those ports, the launcher will warn and stop instead of force-closing an unrelated process.

## First Thing To Click

After the browser opens:

```text
1. Start on Overview.
2. Open Endpoint or DNS Hygiene to inspect evidence-style findings.
3. Open Reports to generate or review output.
4. Open Archive to see saved reports.
5. Open Run History to confirm traceability.
6. Open Redaction to review public-safe output controls.
```

For a guided first run, see:

```text
docs/onboarding/GETTING_STARTED.md
docs/onboarding/FIRST_RUN_CHECKLIST.md
docs/demo/DEMO_WORKFLOW.md
```

## Troubleshooting

If launch fails, read:

```text
docs/onboarding/TROUBLESHOOTING.md
docs/launch/LAUNCHER_REFERENCE.md
```

Common causes:

```text
- Python is not installed or not on PATH.
- Node.js/npm is not installed or not on PATH.
- Another app is using port 8000 or 5173.
- Dependency installation failed due to network or antivirus blocking.
- The browser opened before the frontend fully refreshed.
```

## Validation Commands

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

## Demo Guidance

Use synthetic or local sample evidence only. A good demo should show:

```text
1. Open Overview and explain the local-first positioning.
2. Import or collect one evidence module.
3. Review findings and limitations.
4. Generate a report.
5. Show the Archive and Run History.
6. Show Redaction controls.
7. Run or show the Desktop UI proof ZIP with 10 checked workspaces.
```

More detailed demo guidance is available in:

```text
docs/demo/CUSTOSOPS_DEMO_SCRIPT.md
docs/demo/DEMO_WORKFLOW.md
docs/demo/FINAL_VISUAL_DEMO_NOTES.md
```

## SOC Positioning

CustosOps is positioned as my read-only defensive security evidence console for SMB security hygiene reviews, local evidence analysis and escalation/report generation.

It supports my SOC Analyst development path, but it remains defensive and evidence-focused. I am not positioning it as a SIEM, EDR, MDR/MSSP platform or offensive security tool.

See:

```text
docs/portfolio/CUSTOSOPS_SOC_POSITIONING.md
```

## GitHub Publication Status

This repository is private-first. I should keep it private until manual review is complete.

Before making it public, verify:

```text
- README renders correctly.
- Launcher docs are clear.
- No generated ZIPs or local proof artifacts are tracked.
- No private local paths or workplace/customer names appear.
- Latest tag is present.
```
