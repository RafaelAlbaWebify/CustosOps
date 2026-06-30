# Milestone 4 - Endpoint Report Export v0.1

## Goal

Generate downloadable endpoint security reports from imported endpoint evidence and findings.

## New Backend Endpoint

POST /api/reports/endpoint

Request fields:
- evidence
- findings
- format: html, markdown, or json

Response fields:
- filename
- format
- content_type
- content

## Supported Report Formats

- HTML
- Markdown
- JSON

## Report Sections

- Executive summary
- Severity counts
- Top recommended actions
- Finding details
- Safe next steps
- Limitations
- Report limitations

## Safety

Reports are generated locally by the FastAPI backend.

No cloud upload is performed.

No remediation is performed.

## Current Limitations

- Endpoint reports only.
- No persistent report history yet.
- No PDF export yet.
- No organization branding or logo yet.