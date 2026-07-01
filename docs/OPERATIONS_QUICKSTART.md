# CustosOps Operations Quickstart

## Start CustosOps

PowerShell command:

    .\LAUNCH_CUSTOSOPS.bat

Frontend:

    http://localhost:5173

Backend:

    http://127.0.0.1:8000

## Stop CustosOps

PowerShell command:

    .\STOP_CUSTOSOPS.bat

## Validate the project

PowerShell command:

    .\scripts\validate-foundation.ps1

## Run the doctor

PowerShell command:

    .\scripts\custosops-doctor.ps1

Full doctor with release smoke:

    .\scripts\custosops-doctor.ps1 -Full

## Dependency audit

PowerShell command:

    .\scripts\custosops-dependency-audit.ps1

Safe npm fix attempt:

    .\scripts\custosops-dependency-audit.ps1 -TrySafeNpmFix

## Create a local package

PowerShell command:

    .\scripts\custosops-local-package.ps1

The package ZIP is created on the Desktop and copied to Downloads.

## Safety model

CustosOps is local-first.

The current workflows use local evidence, local reports, and local archives.

CustosOps does not upload evidence externally and does not perform remediation.
