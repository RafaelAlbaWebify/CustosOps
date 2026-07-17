# CustosOps

> Local-first defensive security evidence and reporting console for Windows and Microsoft-oriented support environments.

CustosOps is my SOC / defensive security operations flagship. It is a read-only platform for collecting or importing local evidence, classifying findings, documenting limitations, generating reports, and preparing escalation-ready records for SMB security hygiene reviews and portfolio demonstrations.

The repository is public. Demonstrations and committed fixtures use synthetic or local sample evidence only. CustosOps does not connect to a live Microsoft 365 tenant and does not require production credentials.

## Project Status

CustosOps is approaching its first portfolio-ready `v1.0.0` release.

- Current completion estimate: **90% complete / 10% remaining**
- Current roadmap: [`docs/PROJECT_ROADMAP.md`](docs/PROJECT_ROADMAP.md)
- Release preparation: [`docs/release/V1_RELEASE_PREPARATION.md`](docs/release/V1_RELEASE_PREPARATION.md)
- Current stable baseline: `custosops-v0.31.2-gui-cleanup`

The remaining release work is clean-machine Windows acceptance, final evidence review, and release publication.

## Product Boundary

CustosOps is a read-only defensive evidence console. It is not:

- a SIEM;
- an EDR;
- a vulnerability scanner;
- an MDR/MSSP platform;
- a penetration-testing or exploit framework;
- an auto-remediation platform;
- a live tenant-monitoring service.

Findings include confidence, limitations, and safe next steps. The application does not unlock accounts, reset credentials, change DNS or IP configuration, remediate endpoints, or perform tenant-wide scans.

## Intended Users

- IT support engineers
- Application support engineers
- Security operations learners
- SMB security hygiene reviewers
- Portfolio evaluators

## Workspaces

CustosOps exposes ten UI workspaces:

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

## Evidence and Scenario Coverage

- Endpoint security evidence
- DNS and email-domain hygiene evidence
- Application log evidence
- Windows Event evidence
- IIS/application evidence
- Synthetic Microsoft 365 / Entra-style risky sign-in investigation

The risky sign-in scenario is intentionally backend/API first. It demonstrates the evidence model, analyzer rules, report generation, redaction path, limitations, and tests without claiming live tenant monitoring.

## Core Capabilities

- Read-only local collection and JSON import workflows
- Finding classification with severity, confidence, limitations, and safe next steps
- HTML, Markdown, and JSON report generation
- Report archive
- Evidence run history
- Redaction preview and report-redaction controls
- Repository-owned Playwright workspace and SOC workflow proof
- Clean-machine acceptance evidence with SHA-256 inventory

## Requirements

Recommended for a first run:

- Windows 10 or Windows 11
- PowerShell 5.1 or newer
- Python 3.11 or newer on `PATH`
- Node.js LTS with npm/npx on `PATH`
- Git, when cloning the repository

No Docker, cloud account, external UI-proof package, production credential, or production environment is required.

## Quick Start

From the repository root:

```powershell
.\LAUNCH_CUSTOSOPS.bat
```

On first run, the launcher:

1. Checks ports `8000` and `5173` and safely handles stale CustosOps listeners.
2. Creates the backend virtual environment when missing.
3. Installs backend dependencies when required.
4. Starts the backend and waits for `http://127.0.0.1:8000/api/health`.
5. Installs frontend dependencies when required.
6. Starts the frontend and waits for port `5173`.
7. Opens `http://localhost:5173`.

Keep the backend and frontend PowerShell windows open while using the application.

## Stop CustosOps

```powershell
.\STOP_CUSTOSOPS.bat
```

The stop workflow targets CustosOps listeners on ports `8000` and `5173`. It warns and stops rather than force-closing an unrelated application using either port.

## Guided First Run

After the browser opens:

1. Start on Overview.
2. Open Endpoint or DNS Hygiene and inspect evidence-style findings.
3. Open Reports and generate or review output.
4. Open Archive and Run History to confirm traceability.
5. Open Redaction and review public-safe output controls.

Guides:

- [`docs/onboarding/GETTING_STARTED.md`](docs/onboarding/GETTING_STARTED.md)
- [`docs/onboarding/FIRST_RUN_CHECKLIST.md`](docs/onboarding/FIRST_RUN_CHECKLIST.md)
- [`docs/demo/DEMO_WORKFLOW.md`](docs/demo/DEMO_WORKFLOW.md)
- [`docs/onboarding/TROUBLESHOOTING.md`](docs/onboarding/TROUBLESHOOTING.md)
- [`docs/launch/LAUNCHER_REFERENCE.md`](docs/launch/LAUNCHER_REFERENCE.md)

## Validation

Run the full local repository audit:

```powershell
.\AUDIT_CUSTOSOPS_FULL.bat
```

Run final self-contained clean-machine acceptance:

```powershell
.\ACCEPT_CUSTOSOPS_V1.bat
```

The acceptance workflow:

1. creates a fresh public clone under the Windows temporary directory;
2. validates the documented launch and stop workflows;
3. runs backend tests, contract audits, and the frontend build;
4. installs Playwright Chromium;
5. executes the repository-owned workspace and SOC browser suite;
6. packages Playwright logs/reports and an evidence hash inventory;
7. writes one acceptance ZIP directly to Downloads;
8. removes the temporary clone by default.

Advanced audit command:

```powershell
.\scripts\audit-custosops-local-repo.ps1 -Root . -RunExistingContractAudits -RunBackendTests -RunFrontendBuild
```

Run the browser proof directly while CustosOps is running:

```powershell
cd frontend
npx.cmd playwright install chromium
$env:CUSTOSOPS_BASE_URL = "http://127.0.0.1:5173"
npm.cmd run test:e2e
```

Generated review ZIPs are written directly to Downloads. The workflows do not automatically open the Downloads folder.

## Demo Guidance

Use synthetic or local sample evidence only. A useful demonstration should:

1. Explain the local-first and read-only boundary from Overview.
2. Import or collect one evidence module.
3. Review findings, confidence, and limitations.
4. Generate a report.
5. Show Archive and Run History.
6. Show Redaction controls.
7. Show the passing ten-workspace Playwright proof from the acceptance package.

For the risky-sign-in scenario, emphasize sample evidence, generated findings, report output, limitations, and safe escalation. Do not present it as live tenant monitoring.

More detail:

- [`docs/demo/CUSTOSOPS_DEMO_SCRIPT.md`](docs/demo/CUSTOSOPS_DEMO_SCRIPT.md)
- [`docs/demo/DEMO_WORKFLOW.md`](docs/demo/DEMO_WORKFLOW.md)
- [`docs/demo/FINAL_VISUAL_DEMO_NOTES.md`](docs/demo/FINAL_VISUAL_DEMO_NOTES.md)
- [`docs/portfolio/CUSTOSOPS_SOC_POSITIONING.md`](docs/portfolio/CUSTOSOPS_SOC_POSITIONING.md)

## Public Repository Safety

Before publishing a release or sharing an acceptance package:

- use synthetic or local sample evidence only;
- review generated reports, Playwright logs/reports, and recorded paths;
- confirm no generated ZIP or local proof artifact is tracked;
- confirm no credentials, private local paths, workplace names, or customer names are present;
- run the full audit and clean-machine acceptance workflows;
- record the final evidence package names and SHA-256 hashes.

See [`docs/PROJECT_ROADMAP.md`](docs/PROJECT_ROADMAP.md) for the remaining `v1.0.0` acceptance work.
