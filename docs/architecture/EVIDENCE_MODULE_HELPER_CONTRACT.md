# Evidence Module Helper Contract

CustosOps evidence modules must follow a consistent helper contract before new collectors are added.

This contract applies to Endpoint, DNS, Application Logs, Windows Events, and future IIS/Application local collection work.

## Purpose

The goal is to keep CustosOps scalable as a local-first evidence, posture, and reporting platform.

New evidence modules should not add one-off logic that bypasses findings, reports, archive, redaction, or run history.

## Required backend shape

Each evidence module should have or clearly map to:

```text
schema evidence model
API router
parser or collector where applicable
analyzer that returns findings
report builder
tests for analyzer/import/collector/report behavior
```

## Required platform outputs

Each module should support:

```text
evidence
findings
zero-finding valid state
report generation
archive integration where report generation exists
run history recording
redaction-safe report output
workspace lifecycle coverage
```

## Finding contract

Findings should use the shared SecurityFinding shape:

```text
finding_id
title
severity
confidence
category
affected_asset
evidence
why_it_matters
limitations
safe_next_steps
non_actions
status/review fields
```

## Report contract

Report builders should consistently return:

```text
filename
format
content_type
content
```

Report payloads should include:

```text
report_type
generated_at
summary
evidence
findings
limitations
```

## Run history contract

Evidence workflows should record run history without blocking the operator workflow.

Run records should include:

```text
module_id
module_name
source
source_type
asset
status
raw_count
parsed_count
finding_count
severity counts
warning_count
report_ids
notes
metadata
```

## Redaction contract

Redaction must apply to generated report content and must not mutate source evidence.

Application log reports may use module-specific redaction helpers, but the module must remain compatible with the global report redaction lifecycle.

## Frontend contract

Frontend workspaces should:

```text
load lifecycle state predictably
treat zero findings as valid when evidence exists
make report readiness evidence-based, not finding-count-only
avoid growing App.tsx unless the change is small and low risk
preserve Desktop UI proof coverage
```

## Definition of done for future evidence modules

A new evidence module is not complete until it has:

```text
backend schema
API route
parser or collector path
analyzer tests
report tests
zero-finding behavior
run history behavior
redaction-safe report behavior
archive integration where applicable
workspace lifecycle coverage
Desktop UI proof coverage
```
