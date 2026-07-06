# M31B - GUI Cleanup

Status: complete when validated and tagged.

Purpose:

Clean up the remaining visual issues identified during manual review.

Scope:

```text
- remove duplicated bottom sidebar CustosOps product card
- keep the top sidebar brand as the only product identity block
- center AR/RP archive summary icon text
- replace Findings by Module magnitude bars with Module Health Score
- show each module as a blue/red 10-point score bar
- keep the dashboard viewport fit and all existing workspaces
```

Release tag:

```text
custosops-v0.31.2-gui-cleanup
```

Validation:

```text
frontend build with no CSS syntax warnings
backend tests
platform contract audit
evidence module contract audit
Desktop UI proof with 10 workspaces
UI proof artifact checker
```
