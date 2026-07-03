# Desktop UI Proof Gate

CustosOps uses an external Desktop Playwright UI proof tool as a required UI regression gate before frontend refactors and release tags.

The tool is intentionally kept outside the repository unless explicitly moved later.

Tool location:

```text
C:\Users\ralba\Desktop\CustosOps-UI-Tool
```

Proof ZIP output folder:

```text
C:\Users\ralba\Downloads
```

Standard run command:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Desktop\CustosOps-UI-Tool\Run-CustosOps-UI-Smoke.ps1"
```

Headed run command:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\Desktop\CustosOps-UI-Tool\Run-CustosOps-UI-Smoke.ps1" -Headed
```

Newest proof ZIP listing:

```powershell
Get-ChildItem "$env:USERPROFILE\Downloads" -Filter "CUSTOSOPS_UI_SMOKE_*.zip" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 10 FullName, LastWriteTime, Length
```

A clean proof ZIP must show:

```text
checksOk: true
consoleErrorCount: 0
pageErrorCount: 0
failedRequestCount: 0
workspaceCount: 9 or greater
Backend ready: True
Frontend ready: True
```

Required workspace coverage:

```text
Overview
Endpoint
DNS
App Logs
Windows Events
Reports
Archive
Run History
Redaction
```

The proof must include sidebar click checks and the Redaction preview interaction.

Expected Redaction preview output:

```text
Contact [REDACTED_EMAIL] from C:\Users\[REDACTED_USER]\Desktop
```

Release rule:

```text
No frontend refactor or release tag should be accepted unless frontend build, backend tests, platform audit, and Desktop UI proof all pass.
```

Failure handling:

```text
Do not blindly rerun after a failure.
Inspect console errors, page errors, network failures, screenshots, and HTML snapshots.
Recover to the last stable Git tag if source was left dirty.
```

Current accepted baseline after archive/redaction polish:

```text
custosops-v0.26.10-archive-redaction-ui-polish
```
