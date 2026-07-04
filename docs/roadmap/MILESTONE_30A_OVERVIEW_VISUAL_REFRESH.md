# M30A - Overview Visual Refresh

Status: complete when validated and tagged.

Purpose:

Start the M30 visual-polish track by making the Overview workspace more useful and more demo-ready without changing backend evidence behavior.

Scope:

```text
- Add aggregate Overview metrics derived from existing frontend state.
- Add CSS-only severity distribution bars.
- Add workspace coverage/status cards.
- Add top finding category summary.
- Add recent evidence runs preview.
- Include Windows Events in the Overview coverage.
- Avoid new chart dependencies.
- Avoid backend feature changes.
```

Release tag:

```text
custosops-v0.30.0-overview-visual-refresh
```

Validation:

```text
frontend build
backend tests
platform contract audit
evidence module contract audit
Desktop UI proof with 10 workspaces
UI proof artifact checker
public tracked-file scan
```

Next:

```text
M30B - Severity and findings analytics polish
```