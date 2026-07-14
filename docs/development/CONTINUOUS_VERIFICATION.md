# CustosOps Continuous Verification

CustosOps uses GitHub Actions as the default verification environment so routine development does not depend on repeated local PowerShell packages and manual ZIP uploads.

## Verification policy

Do not request local acceptance testing until every feasible automated check has passed.

Local testing is reserved for behaviour that cannot be reproduced faithfully in GitHub, including real desktop launcher interaction, local security-software interference, Windows collectors against the operator's machine, device integrations, and final analyst UX judgement.

## Linux verification

The Ubuntu job verifies:

- backend dependency installation;
- the complete pytest suite;
- frontend dependency installation;
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
- Markdown report download;
- report archive visibility;
- evidence run-history visibility.

The generated verification artifact contains application logs, test output, Playwright HTML reports, traces and videos on failure, workspace screenshots, SOC workflow screenshots, and the generated Markdown evidence report.

## Windows verification

The native Windows job verifies:

- PowerShell parser validation for every tracked `.ps1` file;
- backend dependency installation;
- the complete pytest suite on Windows;
- frontend dependency installation;
- TypeScript and Vite production build on Windows.

This job validates Windows syntax, path handling, Python behaviour, and frontend build compatibility without using the operator's PC.

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
6. Use retained logs, screenshots, traces, and reports to diagnose failures.
7. Correct the branch and rerun verification.
8. Request one focused local acceptance check only when a genuine local-only risk remains.
