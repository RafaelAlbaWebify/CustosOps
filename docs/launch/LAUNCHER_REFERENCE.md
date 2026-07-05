# CustosOps Launcher Reference

## Main commands

```powershell
.\LAUNCH_CUSTOSOPS.bat
.\STOP_CUSTOSOPS.bat
```

## What LAUNCH_CUSTOSOPS.bat does

The batch file calls:

```text
scripts/launch-custosops.ps1
```

The PowerShell launcher:

```text
1. Checks ports 8000 and 5173.
2. Stops stale CustosOps processes on those ports.
3. Refuses to force-close unrelated processes.
4. Starts the backend window.
5. Waits for backend health.
6. Starts the frontend window.
7. Waits for the frontend port.
8. Opens http://localhost:5173.
```

## What run-backend.ps1 does

```text
1. Enters backend folder.
2. Creates backend\.venv if missing.
3. Installs requirements.txt when requirements change.
4. Checks backend import.
5. Runs uvicorn on 127.0.0.1:8000.
```

## What run-frontend.ps1 does

```text
1. Enters frontend folder.
2. Checks npm.
3. Installs npm dependencies when package files change.
4. Runs Vite on 127.0.0.1:5173.
```

## What STOP_CUSTOSOPS.bat does

The stop command calls:

```text
scripts/stop-custosops.ps1
```

It stops CustosOps-owned listeners on ports 8000 and 5173.

## Safety behavior

The launcher is read-only from a security perspective. It does not scan, exploit, remediate, or change remote systems.

The only local operational action it takes is process management for local development ports.