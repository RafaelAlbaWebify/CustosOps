# CustosOps

> My SOC / defensive security operations flagship.

## Continuous verification

CustosOps uses GitHub Actions as the default verification environment before any local acceptance request.

The automated proof includes:

- backend tests on Linux and Windows;
- deterministic frontend installation with `npm ci`;
- production frontend builds on Linux and Windows;
- PowerShell syntax validation;
- real FastAPI and Vite startup;
- backend health verification;
- Chromium smoke and workspace audits;
- screenshots for all current workspaces;
- browser console-error and failed-request detection;
- an application-log defensive triage workflow;
- analyst disposition and review-note persistence;
- generated Markdown report content verification;
- archive and run-history verification;
- Python and npm dependency vulnerability auditing.

Dependency audits run when dependency files change, can be launched manually, and run weekly after merge into the default branch. Machine-readable audit evidence is retained before the workflow enforces a clean result.

See [`docs/development/CONTINUOUS_VERIFICATION.md`](docs/development/CONTINUOUS_VERIFICATION.md) for the verification policy and proof chain.
