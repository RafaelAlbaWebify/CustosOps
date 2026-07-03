# M26.5D - Evidence Module Helper Contract

Status: complete

Purpose:

Formalize the helper contract that evidence modules must follow before adding IIS/Application local collection.

Scope:

```text
In scope:
- Document the evidence module helper contract.
- Add a project-side evidence contract audit script.
- Validate current module files against the contract.
- Preserve existing runtime behavior.

Out of scope:
- Backend runtime refactors.
- Frontend runtime refactors.
- RedactionSettingsWorkspace extraction.
- IIS/Application local collection implementation.
```

Why this matters:

Endpoint, DNS, Application Logs, and Windows Events already have evidence/report/run-history behavior, but the helper expectations are spread across schemas, APIs, analyzers, services, reports, and tests.

This milestone creates the contract gate needed before M27 adds IIS/Application local collection.

Validation:

```text
1. frontend build
2. backend pytest
3. platform contract audit
4. evidence module contract audit
5. Desktop UI proof smoke
6. UI proof artifact checker
```

Release tag:

```text
custosops-v0.26.13-evidence-helper-contract
```

Next recommended milestone:

```text
M27 - IIS/Application local collection
```
