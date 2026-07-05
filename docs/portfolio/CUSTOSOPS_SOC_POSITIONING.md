# CustosOps SOC Positioning

## Area

```text
SOC - Security Operations
```

## Tool

```text
CustosOps
```

## Current status

```text
In process / future public candidate
```

## Current purpose

CustosOps is a defensive, local-first security evidence console. It helps review evidence, summarize security posture, generate reports, keep run history, and preserve public-safe/redacted outputs.

## What CustosOps currently covers

```text
- Endpoint/security posture evidence.
- DNS hygiene evidence.
- Application log evidence.
- Windows Event evidence.
- IIS/Application evidence.
- Evidence findings and severity handling.
- Report generation.
- Report archive.
- Run history.
- Redaction settings.
- Public-safe review discipline.
```

## What CustosOps partially covers

```text
- SOC/security operations workflow.
- SMB security hygiene reporting.
- Escalation/evidence reports.
- Vulnerability context.
```

Vulnerability context is currently indirect. CustosOps can show posture or evidence issues, but it is not yet a vulnerability scanner or CVE intelligence platform.

## What CustosOps does not yet cover

```text
- Email security checks.
- Risky sign-in review.
- Microsoft 365 / Entra ID sign-in evidence.
- Defender for Office 365 style phishing/quarantine review.
- Automated alert triage.
- Live SOC queue.
- Case management.
- Scheduled collection.
- Agent deployment.
- Multi-tenant MSSP workflow.
```

## Business angle

CustosOps fits best as:

```text
SMB security hygiene and evidence reporting support tool
```

It should not be positioned yet as:

```text
Full MSSP service
Full SOC platform
SIEM replacement
EDR replacement
Vulnerability scanner
```

## Correct positioning statement

CustosOps is a read-only defensive evidence console for SMB security hygiene reviews, local evidence analysis, and escalation/report generation.

## Recommended future SOC roadmap

```text
1. Microsoft 365 / Entra ID evidence import.
2. Risky sign-in review workspace.
3. Email security / phishing evidence workspace.
4. Vulnerability context import from public or exported scanner data.
5. Escalation package generator.
6. Customer-safe executive report template.
7. Optional scheduled evidence snapshot, still read-only.
```

## Guardrails

```text
- Keep read-only by default.
- Keep local-first.
- Avoid offensive/security testing features.
- Avoid automated remediation until the evidence model is mature.
- Preserve redaction and public-safety scans.
```