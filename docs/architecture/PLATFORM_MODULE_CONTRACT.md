# CustosOps Platform Module Contract

CustosOps modules must behave consistently so the platform can scale without turning the frontend into a fragile monolith.

This contract applies to evidence modules such as Endpoint, DNS, Application Logs, Windows Events, and future modules such as IIS/Application local collection and DNS resolver tests.

## Core principles

CustosOps remains:

- Local-first.
- Read-only by default.
- Evidence-oriented.
- Operator-controlled.
- Non-remediating.
- Safe for portfolio/demo use when sample data is used.

## Required module contract

Every evidence module should define or map to the following concepts.

### Identity

- module_id
- module_name
- workspace_id
- source_type
- default_source_label

### State

- evidence state
- findings state
- warnings state
- source state
- loading state if needed
- error/status state if needed

### Input paths

- sample evidence loader
- file import handler
- local collection handler where applicable

### Output paths

- report request builder
- report readiness rule
- run history recorder
- archive integration
- redaction behavior

### Reliability behavior

- Opening a workspace should load required data automatically.
- Manual Refresh may exist, but should not be required for first use.
- Zero findings must be treated as valid evidence when evidence exists.
- Failed collection/import should not mix stale evidence with new failure state.
- Report buttons should be evidence-based, not finding-count-only.
- Redaction must apply to generated report content, not mutate source evidence.
- Run history recording must be non-blocking.

## Workspace lifecycle rule

Each workspace must be covered by the central workspace lifecycle dispatcher.

Expected behavior:

- overview loads module status.
- endpoint loads sample endpoint evidence when no evidence exists.
- dns loads sample DNS evidence when no evidence exists.
- app-log should have explicit lifecycle coverage before more app-log work.
- windows-events loads sample/local state when needed.
- reports and archive load report archive.
- run-history loads run history.
- redaction loads redaction settings.

## Frontend scalability rule

New work should avoid increasing App.tsx complexity unless the change is small and low risk.

Preferred direction:

1. Define module contract and audit.
2. Extract API helpers.
3. Extract workspace components.
4. Extract module-specific workflows.
5. Keep App.tsx as the coordinator, not the implementation of every workflow.

## Backend scalability rule

Backend code should continue using:

- schemas
- services
- API routers
- focused tests

Collectors, parsers, report builders, redaction, and run history should remain separate services.

## Definition of done for new modules

A new module is not done until it has:

- sample or local evidence path
- parser/analyzer tests
- report output
- zero-finding behavior
- run history recording
- redaction-safe report output
- archive behavior where applicable
- workspace lifecycle coverage
- validation proof


## Current Application Logs lifecycle note

The current `app-log` workspace is import-driven.

It has explicit workspace lifecycle coverage, but it does not auto-load sample or local evidence yet.

Before Milestone 27 adds IIS/Application local collection, `app-log` should receive a real local/sample loader that follows the same module contract as Endpoint, DNS, and Windows Events.
