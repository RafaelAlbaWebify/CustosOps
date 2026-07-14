# CustosOps Continuous Verification

CustosOps uses GitHub Actions as the default verification environment so routine development does not depend on repeated local PowerShell packages and manual ZIP uploads.

## Verification policy

Do not request local acceptance testing until every feasible automated check has passed.

Local testing is reserved for behaviour that cannot be reproduced faithfully in GitHub, including real desktop launcher interaction, local security-software interference, Windows collectors against the operator's machine, device integrations, and final analyst UX judgement.

## Linux verification

The Ubuntu job verifies:

- backend dependency installation;
- the complete pytest suite;
- deterministic frontend installation with `npm ci`;
- TypeScript and Vite production build;
- unattended FastAPI startup;
- `/api/health` availability;
- unattended Vite startup;
- Chromium installation;
- application loading;
- browser console errors;
- failed browser requests;
- all current workspace routes;
- full-page screenshots for every workspace;
- an application-log defensive triage workflow;
- operator disposition and review notes;
- Markdown report download and content integrity;
- report archive visibility;
- evidence run-history visibility.

The generated verification artifact contains application logs, test output, Playwright HTML reports, traces and videos on failure, workspace screenshots, SOC workflow screenshots, and the generated Markdown evidence report.

## Windows verification

The native Windows job verifies:

- PowerShell parser validation for every tracked `.ps1` file;
- backend dependency installation;
- the complete pytest suite on Windows;
- deterministic frontend installation with `npm ci`;
- TypeScript and Vite production build on Windows.

This job validates Windows syntax, path handling, Python behaviour, and frontend build compatibility without using the operator's PC.

## Dependency security audit

The dependency audit checks the Python requirements with `pip-audit` and the complete frontend lockfile with `npm audit`.

It runs:

- when Python or frontend dependency files change;
- on manual request;
- every Monday after the workflow is merged into the default branch.

The audit always uploads machine-readable JSON reports and a Markdown summary before enforcing the result. Any reported Python or npm vulnerability fails the audit gate.

The baseline remediation upgraded:

- pytest to the non-vulnerable 9.0.3-or-newer line;
- Vite to 8.1.4;
- `@vitejs/plugin-react` to the compatible 6.0.3 line.

The verified baseline reports zero Python and zero npm vulnerabilities.

## Evidence fixture policy

Tracked fixtures must be synthetic and public-safe.

Use documentation-reserved IP ranges and example domains. Do not commit workplace names, customer names, local usernames, credentials, tokens, production paths, or private infrastructure details.

Fixtures required by automated tests must be explicitly allowed by `.gitignore` and committed to the repository. A test must not depend on an untracked file that happens to exist on one developer machine.

## Current SOC workflow proof

The automated application-log workflow performs:

```text
synthetic log import
-> defensive finding generation
-> analyst disposition
-> analyst review notes
-> Markdown report generation
-> downloaded report content verification
-> local report archive
-> evidence run history
```

The report proof confirms that analyst review metadata is carried into the generated output rather than existing only in browser state.

## Branch and pull-request workflow

1. Create an isolated feature branch.
2. Define the expected automatic proof.
3. Add or update tests.
4. Implement the smallest coherent change.
5. Push and inspect GitHub Actions.
6. Use retained logs, screenshots, traces, security reports, and generated evidence to diagnose failures.
7. Correct the branch and rerun verification.
8. Request one focused local acceptance check only when a genuine local-only risk remains.
