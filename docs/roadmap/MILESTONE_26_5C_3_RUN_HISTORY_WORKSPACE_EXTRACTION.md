# M26.5C-3 - Run History Workspace Extraction

Status: complete

Purpose:

Extract the Run History workspace from App.tsx into a dedicated frontend component while avoiding the failed Redaction extraction path.

Scope:

```text
In scope:
- Move RunHistoryWorkspace to frontend/src/components/RunHistoryWorkspace.tsx.
- Keep App.tsx as owner of run history state and API lifecycle.
- Keep shared formatRunDate helper in App.tsx for Redaction settings.
- Preserve the existing Run History UI copy and behavior.
- Preserve Desktop UI proof coverage.

Out of scope:
- RedactionSettingsWorkspace extraction.
- Backend API changes.
- Evidence run recording logic changes.
- Styling redesign.
```

Validation:

```text
1. frontend build
2. backend pytest
3. platform contract audit
4. Desktop UI proof smoke
5. UI proof artifact checker
```

Release tag:

```text
custosops-v0.26.12-run-history-workspace-extraction
```
