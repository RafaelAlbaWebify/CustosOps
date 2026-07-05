# CustosOps First Run Checklist

Use this checklist before sharing or demonstrating CustosOps.

## Before launch

```text
[ ] Repo is cloned locally.
[ ] Python 3.11 or newer is installed.
[ ] Node.js LTS is installed.
[ ] PowerShell can run python --version.
[ ] PowerShell can run npm --version.
[ ] Ports 8000 and 5173 are not used by another important app.
[ ] No private/customer/employer data is in the repo.
```

## Launch

```text
[ ] Run LAUNCH_CUSTOSOPS.bat from the repository root.
[ ] Backend window opens.
[ ] Frontend window opens.
[ ] Browser opens http://localhost:5173.
[ ] Overview page loads.
```

## Demo path

```text
[ ] Show Overview.
[ ] Show Endpoint.
[ ] Show DNS Hygiene.
[ ] Show Windows Events.
[ ] Show IIS/Application.
[ ] Show Reports.
[ ] Show Archive.
[ ] Show Run History.
[ ] Show Redaction.
```

## Stop

```text
[ ] Run STOP_CUSTOSOPS.bat.
[ ] Backend port 8000 is free.
[ ] Frontend port 5173 is free.
```

## Public or portfolio review

```text
[ ] README current baseline is up to date.
[ ] SOC positioning does not overclaim.
[ ] No generated ZIPs are tracked.
[ ] No sensitive terms appear in tracked files.
[ ] Latest tag is present.
```