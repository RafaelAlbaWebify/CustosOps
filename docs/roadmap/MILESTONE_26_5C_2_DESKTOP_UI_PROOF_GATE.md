# M26.5C-2 - Desktop Playwright UI Proof Gate

Status: complete

Purpose:

Formalize the external Desktop Playwright UI proof tool as a required CustosOps UI regression gate.

Scope:

```text
In scope:
- Document the Desktop UI proof workflow.
- Document proof ZIP expectations.
- Add a project-side proof artifact checker.
- Require this gate before frontend refactors and release tags.

Out of scope:
- Moving the Desktop tool into the repository.
- Refactoring React workspaces.
- Retrying RedactionSettingsWorkspace extraction.
- Changing frontend or backend runtime behavior.
```

Why this milestone matters:

The failed RedactionSettingsWorkspace extraction showed that frontend refactors can leave App.tsx structurally broken while partial files remain behind. The Desktop UI proof tool gives the project a practical release gate that checks the running UI, not only TypeScript compilation.

Required validation:

```text
1. git status --short
2. frontend build
3. backend pytest
4. platform contract audit
5. Desktop UI proof smoke
6. proof ZIP artifact check
```

Release tag:

```text
custosops-v0.26.11-desktop-ui-proof-gate
```

Next recommended milestone:

```text
M26.5C-3 - Run History Workspace extraction
```

Safer extraction workflow:

```text
1. Inspect source first.
2. Create source snapshot/proof.
3. Extract one component only.
4. Run frontend build immediately.
5. Run backend tests.
6. Run platform audit.
7. Run Desktop UI proof.
8. Commit and tag only if all gates pass.
```
