# Milestone 15 - DNS CSV Compatibility Lab v0.1

## Goal

Improve DNS CSV import compatibility without using real company data.

The user does not have a safe real CSV from the old DNS Audit Tool. This milestone creates synthetic compatibility fixtures instead.

## Added

- Downloadable DNS CSV template endpoint.
- Frontend CSV Template button.
- Synthetic DNS CSV compatibility fixtures.
- Backend tests that import each fixture.
- Documentation for safe DNS CSV testing.

## Compatibility Fixtures

Stored under:

samples/dns/compatibility/

Included variants:

- custosops-dns-template.csv
- simulated-old-dns-audit-tool.csv
- semicolon-european-dns-audit.csv
- powershell-export-style-dns-audit.csv
- minimal-dns-audit.csv

## Safety

No real employer or customer data is needed.

Do not use old company DNS exports unless they are fully sanitized and you are allowed to use them.

## Supported Concepts

The importer recognizes common columns for:

- hostname / FQDN / record name
- IP address / record data
- zone / domain / zone name
- DNS server / name server
- forward status
- PTR / reverse DNS status
- ping / reachability
- record age
- duplicate/shared IP flag
- notes/comments

## Next Step

Use these synthetic fixtures to keep improving the importer, then later test with a deliberately sanitized CSV if one is created from a lab environment.