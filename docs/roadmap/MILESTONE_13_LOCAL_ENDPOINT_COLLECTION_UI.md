# Milestone 13 - Local Endpoint Collection from UI v0.1

## Goal

Allow CustosOps to run the read-only local endpoint evidence collector directly from the UI.

## Added

- Backend service to run the PowerShell endpoint collector.
- POST /api/endpoint/collect-local
- Frontend "Collect Local" button in Endpoint Security Evidence.
- Automatic analysis of collected endpoint evidence.
- Evidence saved to reports/endpoint-evidence.local.json.

## Workflow

Click:

Collect Local

CustosOps then:

1. Runs collectors/powershell/endpoint/Get-EndpointSecurityEvidence.ps1
2. Saves reports/endpoint-evidence.local.json
3. Validates the evidence schema
4. Analyzes findings
5. Updates the Endpoint panel

## Safety

The collector remains read-only.

It does not:

- change endpoint configuration
- remediate findings
- collect passwords
- upload evidence to cloud storage

## Limitation

This is local single-machine collection only.

Remote endpoint collection is not implemented.