# M32 - Risky Sign-In Evidence Review

Status: backend/API scenario added; local validation still required.

Purpose:

Add the first explicit SOC Analyst scenario to CustosOps: read-only review of Microsoft 365 / Entra-style risky sign-in evidence.

Why this is high ROI:

```text
- It connects directly to Microsoft 365, Entra ID, identity, endpoint, and support background.
- It demonstrates SOC-style triage without offensive functionality.
- It uses synthetic/public-safe sample evidence.
- It creates natural interview material around alert triage, evidence review, severity, confidence, limitations, and escalation.
```

Implemented scope:

```text
- backend/app/schemas/risky_signin.py
- backend/app/analyzers/risky_signin_evidence.py
- backend/app/api/risky_signins.py
- backend/app/schemas/risky_signin_report.py
- backend/app/services/risky_signin_report.py
- samples/risky_signins/sample-risky-signins.json
- backend/tests/test_risky_signin_evidence.py
- FastAPI router registration
- /api/reports/risky-signins report endpoint
```

Initial API flow:

```text
GET  /api/risky-signins/sample-evidence
GET  /api/risky-signins/sample-findings
POST /api/risky-signins/import
POST /api/risky-signins/analyze
POST /api/reports/risky-signins
```

Initial finding rules:

```text
- Active high-risk sign-in evidence needs review.
- Risky successful sign-in without confirmed MFA satisfaction.
- Legacy client application sign-in evidence.
- Repeated failed sign-in evidence for one or more users.
- Same user has sign-in evidence from multiple countries.
- No major risky sign-in findings info result when no rule triggers.
```

Safety boundaries:

```text
- No live Microsoft tenant connection.
- No credential, token, or secret collection.
- No account disablement.
- No password reset.
- No session revocation.
- No Conditional Access modification.
- No claim that a risky sign-in proves compromise by itself.
```

SOC analyst story:

```text
CustosOps can now show how I triage an identity alert safely:
1. Start from an alert-like evidence set.
2. Review user, location, IP, device, application, risk level, MFA, and Conditional Access result.
3. Classify findings with severity and confidence.
4. State limitations clearly.
5. Produce safe next steps and escalation notes.
6. Avoid unsafe remediation from the tool.
```

Validation command:

```powershell
.\scripts\audit-custosops-local-repo.ps1 -Root . -RunExistingContractAudits -RunBackendTests -RunFrontendBuild
```

Minimum backend validation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Completion criteria:

```text
- risky sign-in tests pass locally
- full backend test suite passes locally
- local repo audit ZIP reviewed
- sample evidence remains synthetic/public-safe
- README and demo notes explain this as read-only SOC triage evidence
```

Recommended next step:

```text
M32B - Risky Sign-In Demo Notes and Escalation Package
```

M32B should add a short demo script, escalation note, and sample analyst summary for the risky sign-in scenario before building a full UI workspace.
