# M31 - Beginner Runbook and Launch Audit

Status: complete when validated and tagged.

Purpose:

Make the private GitHub repository easier for a non-expert reviewer to launch, understand, and evaluate.

Scope:

```text
- Update README to the current baseline.
- Add beginner requirements and first-run flow.
- Verify and improve launch/stop batch files.
- Make launcher safer around ports 8000 and 5173.
- Add dependency hash checks for backend and frontend installs.
- Add Getting Started, First Run Checklist, Troubleshooting, Launcher Reference, and Demo Workflow docs.
- Update stale release/portfolio docs from older baselines.
- Preserve read-only defensive positioning.
```

Release tag:

```text
custosops-v0.31.0-beginner-runbook-launch-audit
```

Validation:

```text
frontend build
backend tests
platform contract audit
evidence module contract audit
Desktop UI proof with 10 workspaces
UI proof artifact checker
public tracked-file scan
```

Next:

```text
Manual GitHub rendered-doc review, then optional M32 Microsoft 365 / Entra evidence import.
```