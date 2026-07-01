# CustosOps Local Launch Workflow

## Launch

Double-click:

LAUNCH_CUSTOSOPS.bat

or use the Desktop shortcut:

Launch CustosOps

This starts:

- backend on http://127.0.0.1:8000
- frontend on http://localhost:5173

The launcher opens two PowerShell windows:

- one for FastAPI backend
- one for Vite frontend

It then opens the browser automatically.

## Stop

Double-click:

STOP_CUSTOSOPS.bat

or use the Desktop shortcut:

Stop CustosOps

This stops local processes listening on:

- port 8000
- port 5173

## Notes

The launcher does not run CustosOps as a Windows service.

It is a local development and portfolio demo launcher.

Closing the backend or frontend PowerShell windows stops the app.