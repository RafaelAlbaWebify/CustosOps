# Milestone 5 - DNS Hygiene v0.1

## Goal

Start fusing the old DNS Audit Tool concept into CustosOps as a DNS and Infrastructure Hygiene module.

## Scope

This milestone adds:

- DNS evidence schema
- DNS hygiene analyzer
- Synthetic DNS sample evidence
- DNS API routes
- Backend tests

## New API Endpoints

- GET /api/dns/sample-evidence
- GET /api/dns/sample-findings
- POST /api/dns/analyze

## Initial Finding Rules

- Forward DNS not OK
- PTR missing or mismatched
- Potential stale record
- Shared IP review required

## Safety

DNS Hygiene v0.1 is analysis-only.

It does not:

- change DNS records
- delete DNS records
- create DNS records
- query production DNS directly
- perform remediation

## Current Limitations

- No direct import from DNS Audit CSV yet.
- No real DNS collector in CustosOps yet.
- No DNS report export yet.
- No public DNS exposure checks yet.

## Next Step

Add DNS Audit CSV import so CustosOps can consume outputs from the old dns-audit-tool repository.