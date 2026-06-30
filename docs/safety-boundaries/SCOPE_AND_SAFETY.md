# CustosOps Scope and Safety Boundaries

## In Scope

CustosOps collects and analyzes read-only cybersecurity evidence from Microsoft and Windows-oriented environments.

Initial scope:
- Windows endpoint security evidence
- DNS and infrastructure hygiene evidence
- Identity and Microsoft 365 security posture evidence
- Risk prioritization
- Remediation guidance
- HTML, JSON, CSV, and Markdown reporting

## Out of Scope

CustosOps is not:

- a penetration-testing tool
- an exploit framework
- an antivirus
- an EDR
- a SIEM
- a vulnerability scanner from scratch
- an automatic patching platform
- a cloud security posture management platform
- a replacement for Microsoft Defender, Intune, Sentinel, or enterprise tooling

## Safety Rules

- No offensive testing.
- No credential collection.
- No credential storage.
- No customer-specific data in public samples.
- No automatic remediation in v1.
- No public internet scanning without explicit authorization.
- No claims of guaranteed compliance.
- No claims of confirmed vulnerability without validation.

## Output Standard

Each finding should include:
- observed evidence
- severity
- confidence
- why it matters
- limitations
- safe next steps
- non-actions