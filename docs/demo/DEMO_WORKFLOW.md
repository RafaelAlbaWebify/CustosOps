# CustosOps Demo Workflow

This workflow is for a first-time reviewer.

## Start

```powershell
.\LAUNCH_CUSTOSOPS.bat
```

Wait until the browser opens:

```text
http://localhost:5173
```

## Walkthrough

Use this order:

```text
1. Overview
2. Endpoint
3. DNS Hygiene
4. App Logs
5. Windows Events
6. IIS/Application
7. Reports
8. Archive
9. Run History
10. Redaction
```

## What to say

CustosOps is a local-first defensive evidence console. It is useful for SMB security hygiene reviews and support/escalation reporting.

## What to avoid claiming

Do not claim CustosOps is:

```text
- a SIEM
- an EDR
- a vulnerability scanner
- an MDR/MSSP service
- an offensive testing tool
- an auto-remediation platform
```

## Stop

```powershell
.\STOP_CUSTOSOPS.bat
```