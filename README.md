# CustosOps

CustosOps is a local-first cybersecurity evidence and posture platform for Microsoft and Windows environments.

It collects read-only endpoint, DNS, identity, and Microsoft 365 security evidence, classifies cyber hygiene findings, and generates remediation-ready reports.

## Positioning

CustosOps is not a penetration-testing tool, exploit framework, SIEM, EDR, vulnerability scanner, or auto-remediation platform.

It is designed to demonstrate and support:

- cybersecurity evidence collection
- endpoint security posture review
- DNS and infrastructure hygiene review
- identity and Microsoft 365 security evidence
- risk prioritization
- remediation guidance
- support-ready reporting
- safe read-only operational workflows

## Initial Modules

1. Endpoint Security Evidence
2. DNS and Infrastructure Hygiene
3. Identity and M365 Security Posture
4. Risk and Vulnerability Prioritization
5. Reports and Remediation Runbooks

## Migration Sources

The following existing repositories may be fused into CustosOps later:

- endpoint-support-checklist-powershell
- dns-audit-tool
- selected TRACE architecture and diagnostics patterns
- selected enterprise support lab scenarios

JOLT remains separate.

## Safety Principles

- Read-only first.
- Evidence before conclusion.
- Findings must include confidence and limitations.
- No exploitation.
- No credential storage.
- No automatic remediation in the first public version.
- No customer or employer-specific data.