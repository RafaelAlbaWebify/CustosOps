# CustosOps Troubleshooting

## Launch does nothing

Run from PowerShell instead of double-clicking:

```powershell
.\LAUNCH_CUSTOSOPS.bat
```

If it fails, read the message in the terminal.

## Python was not found

Install Python 3.11 or newer. During installation, enable:

```text
Add python.exe to PATH
```

Then close and reopen PowerShell.

Check:

```powershell
python --version
```

## npm was not found

Install Node.js LTS. It includes npm.

Then close and reopen PowerShell.

Check:

```powershell
npm --version
```

## Backend did not become healthy

Check the backend PowerShell window.

Common causes:

```text
- Python missing from PATH.
- pip install failed.
- antivirus or network blocked dependency installation.
- backend import failed.
- port 8000 is already used.
```

Reset backend dependencies:

```powershell
cd backend
Remove-Item .venv -Recurse -Force
Remove-Item .deps_installed.hash -Force -ErrorAction SilentlyContinue
cd ..
.\LAUNCH_CUSTOSOPS.bat
```

## Frontend did not open port 5173

Check the frontend PowerShell window.

Common causes:

```text
- Node.js/npm missing from PATH.
- npm install failed.
- port 5173 is already used.
```

Reset frontend dependencies:

```powershell
cd frontend
Remove-Item node_modules -Recurse -Force
Remove-Item .deps_installed.hash -Force -ErrorAction SilentlyContinue
cd ..
.\LAUNCH_CUSTOSOPS.bat
```

## Port 8000 or 5173 is already used

CustosOps uses:

```text
8000 for backend
5173 for frontend
```

The launcher will not force-close a process that does not look like CustosOps.

To inspect listeners:

```powershell
Get-NetTCPConnection -LocalPort 8000,5173 -State Listen
```

Close the app using the port, then launch CustosOps again.

## Browser does not open

Open it manually:

```text
http://localhost:5173
```

## How to stop CustosOps

Run:

```powershell
.\STOP_CUSTOSOPS.bat
```

If that fails, close the backend and frontend PowerShell windows manually.