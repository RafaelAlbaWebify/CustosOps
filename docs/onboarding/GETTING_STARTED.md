# Getting Started with CustosOps

This guide is for a first-time user who wants to run CustosOps locally on Windows.

## 1. Install requirements

Install these first:

```text
- Python 3.11 or newer
- Node.js LTS, which includes npm
- Git, if you are cloning the repository
```

After installation, close and reopen PowerShell.

Check the commands:

```powershell
python --version
npm --version
git --version
```

## 2. Open the repository folder

```powershell
cd <path-to-custosops>
```

## 3. Launch the app

```powershell
.\LAUNCH_CUSTOSOPS.bat
```

The first launch can take longer because CustosOps may install Python and npm dependencies.

## 4. What should happen

You should see:

```text
- one backend PowerShell window
- one frontend PowerShell window
- a browser tab opened at http://localhost:5173
```

Keep the backend and frontend windows open.

## 5. First thing to click

Use this simple path:

```text
1. Overview
2. Endpoint
3. DNS Hygiene
4. Reports
5. Archive
6. Run History
7. Redaction
```

## 6. Stop the app

```powershell
.\STOP_CUSTOSOPS.bat
```

## 7. If something fails

Read:

```text
docs/onboarding/TROUBLESHOOTING.md
docs/launch/LAUNCHER_REFERENCE.md
```