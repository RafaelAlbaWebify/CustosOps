# CustosOps v1 Acceptance Notes

The v1 acceptance path is self-contained in this repository.

Run from the repository root on Windows:

```powershell
.\ACCEPT_CUSTOSOPS_V1.bat
```

The runner creates a fresh public clone, validates launch and stop behavior, runs the full local audit, installs Playwright Chromium, executes the repository-owned workspace/SOC browser suite, records SHA-256 hashes for generated audit packages, and writes one acceptance ZIP directly to Downloads.

No external `CustosOps-UI-Tool` folder or script is required.

A successful package is named:

```text
CUSTOSOPS_V1_ACCEPTANCE_<timestamp>.zip
```

A failed run creates:

```text
CUSTOSOPS_V1_ACCEPTANCE_FAILED_<timestamp>.zip
```

The acceptance ZIP contains:

- `ACCEPTANCE_SUMMARY.txt`;
- `ACCEPTANCE_RESULT.json`;
- Playwright standard-output and standard-error logs;
- the Playwright HTML report when generated;
- Playwright test-result artifacts when generated.

The separate local audit ZIP remains directly in Downloads and is referenced with its SHA-256 hash in the acceptance summary.
