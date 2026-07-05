# M30G - Professional Dashboard Layout

Status: complete when validated and tagged.

Purpose:

Make the real CustosOps Overview look closer to the approved professional dashboard mock without compromising practicality.

Scope:

```text
- Replace the tall Overview stack with a compact command-center dashboard.
- Keep the collapsible sidebar from M30F.
- Add a compact header and top action.
- Use a 5-card KPI row.
- Put severity distribution, module health, and findings-by-module in one row.
- Put recent evidence runs, archive/report summary, and priority findings in a second row.
- Use CSS-only donut and bar visuals.
- Keep detailed operational workspaces available from navigation.
- Avoid backend changes and chart dependencies.
```

Release tag:

```text
custosops-v0.30.6-professional-dashboard-layout
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
M30H - Final visual demo package
```