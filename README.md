# CustosOps

CustosOps is a local-first defensive security evidence console for Windows and Microsoft support environments.

It structures evidence from endpoint, DNS, application-log, Windows-event, IIS/application, reporting, redaction, history, and archive workflows. The project uses synthetic public-safe samples and does not require production credentials or private infrastructure data.

## Start the application

On Windows, run:

```text
START-CUSTOSOPS.cmd
```

The launcher starts:

- FastAPI backend: `http://127.0.0.1:8000`
- Backend health endpoint: `http://127.0.0.1:8000/api/health`
- React frontend: `http://127.0.0.1:5173`

## Continuous verification

GitHub Actions verifies routine development without requiring repeated local PowerShell packages or manual ZIP uploads.

The automated proof includes:

- repository syntax and structure hygiene;
- Python backend tests on Linux and Windows;
- deterministic frontend installation with `npm ci`;
- TypeScript and Vite production builds on Linux and Windows;
- PowerShell parser validation;
- unattended FastAPI and Vite startup;
- backend health checks;
- Chromium smoke and workspace audits;
- browser console-error and failed-request detection;
- screenshots for all current workspaces;
- a complete application-log defensive triage workflow;
- analyst disposition and review-note persistence;
- Markdown report download and content verification;
- archive and run-history verification;
- Python and npm dependency-security audits;
- zero-vulnerability enforcement after retained evidence upload;
- CycloneDX supply-chain inventories for Python and npm dependencies;
- grouped weekly Dependabot maintenance for Python, npm, and GitHub Actions.

The current verified baseline reports:

- 71 backend tests passing on Linux and Windows;
- 0 Python dependency vulnerabilities;
- 0 npm dependency vulnerabilities;
- 26 Python components in the CycloneDX inventory;
- 31 frontend npm components in the CycloneDX inventory.

Generated GitHub artifacts retain logs, reports, browser traces, screenshots, security-audit JSON, CycloneDX SBOM files, and Windows verification evidence.

Local testing is reserved for behaviour that cannot be reproduced faithfully in GitHub, such as real desktop launcher interaction, endpoint-security interference, Windows collectors against the operator machine, device integrations, and final analyst UX judgement.

See [`docs/development/CONTINUOUS_VERIFICATION.md`](docs/development/CONTINUOUS_VERIFICATION.md) for the verification, security, maintenance, and evidence policy.
