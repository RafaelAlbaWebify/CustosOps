# CustosOps Continuous Verification

CustosOps uses GitHub Actions as the default verification environment so routine development does not depend on repeated local PowerShell packages and manual ZIP uploads.

## Verification policy

Do not request local acceptance testing until every feasible automated check has passed.

Local testing is reserved for behaviour that cannot be reproduced faithfully in GitHub, including real desktop launcher interaction, local security-software interference, Windows collectors against the operator's machine, device integrations, and final analyst UX judgement.

## Repository hygiene gate

A fast Ubuntu job runs before the heavier Linux and Windows verification jobs. It verifies:

- Python source and tests compile successfully;
- frontend `package.json` and `package-lock.json` parse as valid JSON;
- GitHub workflow and configuration files parse as valid YAML;
- no unresolved Git merge-conflict markers remain in tracked files.

The Linux and Windows verification jobs depend on this gate, so malformed repository state fails before browser installation or cross-platform builds consume additional time.

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

## Supply-chain inventory

The supply-chain workflow generates CycloneDX JSON inventories for the Python requirements and the complete npm dependency graph.

It runs when dependency manifests or its workflow change, on manual request, and every Monday after merge into the default branch. The inventories and Markdown component summary are retained for 30 days.

The verified baseline contains 26 Python components and 31 frontend npm components. Both inventories validate as CycloneDX documents and include unique serial numbers.

The SBOM answers which components are present. The dependency audit separately checks whether those dependency ecosystems currently report known vulnerabilities.

## Automated dependency maintenance

Dependabot checks three ecosystems every Monday in the `Europe/Madrid` timezone:

- Python dependencies in `/backend`;
- npm dependencies in `/frontend`;
- GitHub Actions used by repository workflows.

Minor and patch updates are grouped by ecosystem to reduce pull-request noise. Major upgrades remain separate so compatibility changes receive focused review.

Dependabot pull requests are not trusted merely because they were generated automatically. They must pass the same repository-hygiene, backend, deterministic frontend, browser, Windows, dependency-security, and supply-chain gates that apply to human-authored changes.

## Pull-request evidence policy

The repository pull-request template requires authors to state:

- purpose and scope;
- automated evidence completed;
- public-safe data review;
- whether any local-only acceptance risk remains;
- rollback or recovery considerations.

Local testing must identify one narrow risk and expected result. It must not replace available GitHub verification.

## Scope-integrity review

Before declaring an infrastructure PR complete, compare it with the target branch and review disproportionate additions or deletions. Automation work must not silently replace product, launcher, troubleshooting, demo, or publication documentation.

The verification-baseline PR used this review to detect and reverse an unintended replacement of the operational README. The original README is preserved byte-for-byte; detailed automation guidance remains in this document and the pull-request evidence.

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
6. Use retained logs, screenshots, traces, security reports, SBOMs, and generated evidence to diagnose failures.
7. Compare the feature branch with its target and inspect disproportionate changes for scope loss.
8. Correct the branch and rerun verification.
9. Request one focused local acceptance check only when a genuine local-only risk remains.
