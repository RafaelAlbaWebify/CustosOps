# M30F - Dashboard Fit and Collapsible Sidebar

Status: complete when validated and tagged.

Purpose:

Move CustosOps closer to the professional dashboard mock by improving the real GUI, not by generating another mock.

Scope:

```text
- Add collapsible sidebar behavior similar to modern app shells.
- Keep the sidebar expanded by default for usability and proof stability.
- Add compact collapsed navigation rail.
- Add topbar evidence-source action.
- Convert page scrolling to app-internal scrolling.
- Compact the Overview dashboard so the primary dashboard fits better inside the browser viewport.
- Hide duplicated lower Overview summary sections while preserving workspace navigation and detailed workspaces.
- Avoid backend changes and chart dependencies.
```

Release tag:

```text
custosops-v0.30.5-dashboard-fit-collapsible-sidebar
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
M30G - Final visual demo package
```