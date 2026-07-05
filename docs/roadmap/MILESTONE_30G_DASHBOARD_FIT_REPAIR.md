# M30G Repair - Professional Dashboard Fit

Status: complete when validated and tagged.

Purpose:

Repair the first professional dashboard layout pass. The previous pass passed validation but the proof screenshot showed that the dashboard collapsed into a vertical stack at the normal browser width.

Scope:

```text
- Keep the professional dashboard grid active at the normal proof/browser width.
- Keep the 5-card KPI row.
- Fit severity, module health, and findings-by-module in one row.
- Fit recent runs, archive summary, and top findings in one row.
- Reduce card, legend, table, and row density.
- Fix severity legend overlap caused by reusable SeverityDot text.
- Keep collapsible sidebar and detailed workspaces.
- Avoid backend changes and chart dependencies.
```

Release tag:

```text
custosops-v0.30.7-professional-dashboard-fit-repair
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
Manual visual review, then M30H final visual demo package.
```