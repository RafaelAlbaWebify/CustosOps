# CustosOps Project Roadmap

## Completion target

This roadmap defines **project completion** as a public, portfolio-ready `v1.0` release of the existing local-first defensive evidence console.

It does not treat CustosOps as a SIEM, EDR, vulnerability scanner, live Microsoft 365 monitoring service, auto-remediation platform, or commercial multi-tenant SaaS product. Those are outside the stated project scope.

## Current completion estimate

**Estimated complete: 88%**  
**Estimated remaining: 12%**

The percentage is a weighted engineering estimate against the `v1.0` target below. It is not based on commit count or lines of code.

| Workstream | Weight | Current status | Earned |
|---|---:|---|---:|
| Core local-first platform and API | 20% | Complete | 20% |
| Evidence modules and finding model | 20% | Complete | 20% |
| Ten-workspace frontend experience | 15% | Complete | 15% |
| Reports, archive, history and redaction | 15% | Complete | 15% |
| Automated tests, Linux/Windows CI, audits and SBOM | 15% | Complete | 15% |
| Public documentation and onboarding | 5% | Mostly complete; publication wording needs final alignment | 4% |
| Release packaging, versioning and public release evidence | 5% | Partially complete | 2% |
| Clean-machine acceptance and final demo proof | 5% | Partially complete | 2% |
| **Total** | **100%** |  | **88%** |

## Completed baseline

- Read-only local evidence collection and JSON import workflows.
- Endpoint, DNS, application log, Windows Event, IIS/application and risky sign-in evidence scenarios.
- Finding classification with severity, confidence, limitations and safe next steps.
- HTML, Markdown and JSON reporting.
- Report archive and evidence run history.
- Redaction preview and report-redaction controls.
- Ten UI workspaces.
- Windows launcher and stop scripts.
- Local audit and full proof launchers.
- Backend test suite.
- Deterministic frontend install and build.
- Playwright workspace and SOC workflow coverage.
- Linux and Windows continuous verification.
- Python and npm dependency audits.
- CycloneDX supply-chain inventories.
- Public-safe fixtures and repository history review.
- TypeScript 7 migration.
- Aligned React 19 migration.

## Remaining `v1.0` work

### 1. Align public documentation

- Replace the obsolete README statement that the repository is private-first.
- State that the repository is public and uses synthetic/local sample evidence only.
- Link this roadmap from the README.
- Confirm every onboarding and demo document reflects the current commands and workspaces.

### 2. Run final clean-machine acceptance

On a clean or newly prepared Windows environment:

- Clone the public repository.
- Run `LAUNCH_CUSTOSOPS.bat` without pre-existing virtual environments or `node_modules`.
- Exercise the guided first-run path.
- Stop the application with `STOP_CUSTOSOPS.bat`.
- Run `AUDIT_CUSTOSOPS_FULL.bat`.
- Run `PROVE_CUSTOSOPS_FULL.bat` with the companion UI proof tool.
- Confirm all evidence ZIPs are produced directly in Downloads.

### 3. Produce final public proof package

- Capture the current ten-workspace UI proof after React 19 and TypeScript 7.
- Review screenshots, browser logs, network logs and workspace checks.
- Confirm no private paths, names, credentials or non-synthetic evidence appear.
- Retain one final release evidence package outside the repository.

### 4. Create the `v1.0` release

- Decide the final version number and update the stable-baseline documentation.
- Create an annotated release tag from a fully green `master` commit.
- Publish concise release notes covering scope, limitations, setup and validation.
- Confirm the release page and README are understandable to a recruiter or first-time evaluator.

### 5. Final portfolio review

- Verify repository description, topics and social preview.
- Verify the first five minutes of the demo tell a coherent SOC/application-support story.
- Confirm limitations are prominent and no live-monitoring or remediation claims are implied.
- Link the public repository from the intended portfolio or professional profile only after the final proof review.

## `v1.0` completion criteria

CustosOps reaches 100% for this roadmap when:

1. `master` is green in all continuous verification, audit and inventory workflows.
2. The public README and onboarding documentation match the real repository state.
3. A clean-machine Windows launch, stop, audit and UI proof have passed.
4. The final proof artifacts have been manually reviewed for public safety.
5. A tagged GitHub release exists with accurate scope and limitations.
6. There are no unresolved release-blocking issues or pull requests.

## Post-`v1.0` ideas

These are optional future enhancements and do not reduce the `v1.0` completion percentage:

- Additional synthetic investigation scenarios.
- More report templates.
- Accessibility improvements.
- Expanded browser coverage.
- Installer or portable packaging research.
- Additional import adapters that preserve the local-first, read-only boundary.
