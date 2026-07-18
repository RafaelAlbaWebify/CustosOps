# CustosOps

> Local-first defensive security evidence and reporting console for Windows and Microsoft-oriented support environments.

CustosOps is a read-only platform for collecting or importing local evidence, classifying findings, documenting limitations, generating reports, and preparing escalation-ready records for SMB security hygiene reviews and portfolio demonstrations.

The repository is public. Demonstrations and committed fixtures use synthetic or local sample evidence only. CustosOps does not connect to a live Microsoft 365 tenant and does not require production credentials.

## Project status

- `v1.0.0`: published and clean-machine accepted.
- Current `master`: completed TRACE-aligned GUI and post-v1 maintenance baseline.
- Next release: `v1.1.0` presentation and assurance package.
- Roadmap: [`docs/PROJECT_ROADMAP.md`](docs/PROJECT_ROADMAP.md)
- v1.1 preparation: [`docs/release/V1_1_RELEASE_PREPARATION.md`](docs/release/V1_1_RELEASE_PREPARATION.md)

## Final interface

The completed interface uses a responsive, light operational-console visual system aligned with the TRACE portfolio application.

![CustosOps Overview](docs/images/custosops-overview.jpg)

![CustosOps evidence and governance workspaces](docs/images/custosops-workspaces.jpg)

## Product boundary

CustosOps is a read-only defensive evidence console. It is not:

- a SIEM;
- an EDR;
- a vulnerability scanner;
- an MDR/MSSP platform;
- a penetration-testing or exploit framework;
- an auto-remediation platform;
- a live tenant-monitoring service.

Findings include confidence, limitations, and safe next steps. The application does not unlock accounts, reset credentials, change DNS or IP configuration, remediate endpoints, or perform tenant-wide scans.

## Intended users

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

## Core capabilities

- Read-only local collection and JSON import workflows
- Finding classification with severity, confidence, limitations, and safe next steps
- Endpoint, DNS, application-log, Windows-event, and IIS/application evidence
- Synthetic Microsoft 365 / Entra-style risky sign-in investigation
- HTML, Markdown, and JSON report generation
- Report archive and evidence run history
- Redaction preview and report-redaction controls
- Repository-owned Playwright workspace and SOC workflow proof
- Linux and Windows CI validation
- Dependency security audit and supply-chain inventory
- Clean-machine acceptance evidence with SHA-256 inventory

The risky-sign-in scenario is intentionally backend/API first. It demonstrates the evidence model, analyzer rules, report generation, redaction path, limitations, and tests without claiming live tenant monitoring.

## Requirements

Recommended for a first run:

- Windows 10 or Windows 11
- PowerShell 5.1 or newer
- Python 3.11 or newer on `PATH`
- Node.js LTS with npm/npx on `PATH`
- Git, when cloning the repository

No Docker, cloud account, external UI-proof package, production credential, or production environment is required.

## Quick start

From the repository root:

```powershell
.\LAUNCH_CUSTOSOPS.bat
```

On first run, the launcher:

1. checks ports `8000` and `5173` and safely handles stale CustosOps listeners;
2. creates the backend virtual environment when missing;
3. installs backend dependencies when required;
4. starts the backend and waits for `http://127.0.0.1:8000/api/health`;
5. installs frontend dependencies when required;
6. starts the frontend and waits for port `5173`;
7. opens `http://localhost:5173`.

Keep the backend and frontend PowerShell windows open while using the application.

## Stop CustosOps

```powershell
.\STOP_CUSTOSOPS.bat
```

The stop workflow targets CustosOps listeners on ports `8000` and `5173`. It warns and stops rather than force-closing an unrelated application using either port.

## Five-minute evaluator path

Use [`docs/evaluator/FIVE_MINUTE_EVALUATOR_PATH.md`](docs/evaluator/FIVE_MINUTE_EVALUATOR_PATH.md) for the fastest complete review.

A useful manual path is:

1. confirm the read-only boundary on Overview;
2. review Endpoint and DNS findings, confidence, evidence, and limitations;
3. follow the App Logs support workflow;
4. inspect Reports, Archive, and Run History;
5. review Redaction controls;
6. verify the automated engineering evidence.

Additional guides:

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

Run self-contained clean-machine acceptance:

```powershell
.\ACCEPT_CUSTOSOPS_V1.bat
```

The acceptance workflow creates a fresh public clone, validates launch and stop, runs backend/frontend/browser verification, packages logs and hashes, writes one ZIP directly to Downloads, and removes the temporary clone by default.

Run the browser suite directly while CustosOps is running:

```powershell
cd frontend
npx.cmd playwright install chromium
$env:CUSTOSOPS_BASE_URL = "http://127.0.0.1:5173"
npm.cmd run test:e2e
```

Run the committed visual-regression baseline after it has been generated and reviewed:

```powershell
$env:CUSTOSOPS_VISUAL_REGRESSION = "1"
npm.cmd run test:e2e
```

Generated review ZIPs are written directly to Downloads. The workflows do not automatically open the Downloads folder.

## Demo guidance

Use synthetic or local sample evidence only. Demonstrations should explain the local-first boundary, review one evidence module, show confidence and limitations, generate a report, show Archive and Run History, and finish with Redaction and passing browser proof.

More detail:

- [`docs/demo/CUSTOSOPS_DEMO_SCRIPT.md`](docs/demo/CUSTOSOPS_DEMO_SCRIPT.md)
- [`docs/demo/DEMO_WORKFLOW.md`](docs/demo/DEMO_WORKFLOW.md)
- [`docs/demo/FINAL_VISUAL_DEMO_NOTES.md`](docs/demo/FINAL_VISUAL_DEMO_NOTES.md)
- [`docs/portfolio/CUSTOSOPS_SOC_POSITIONING.md`](docs/portfolio/CUSTOSOPS_SOC_POSITIONING.md)

## Public repository safety

Before publishing a release or sharing an acceptance package:

- use synthetic or local sample evidence only;
- review generated reports, Playwright logs/reports, screenshots, and recorded paths;
- confirm no generated ZIP or local proof artifact is tracked;
- confirm no credentials, private local paths, workplace names, or customer names are present;
- run the full audit and clean-machine acceptance workflows;
- record the final evidence package names and SHA-256 hashes.
