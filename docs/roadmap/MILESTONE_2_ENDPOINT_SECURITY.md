# Milestone 2 - Endpoint Security Evidence v0.1

## Goal

Add the first real CustosOps security module.

This milestone introduces a read-only Windows endpoint evidence collector and backend analyzer rules for endpoint security posture.

## Collector

Path:

collectors/powershell/endpoint/Get-EndpointSecurityEvidence.ps1

The collector gathers:

- computer identity
- OS version and build
- BIOS version
- Secure Boot status
- TPM status
- BitLocker status
- Defender status
- Windows Firewall profiles
- local administrators
- RDP status
- SMBv1 status
- listening ports
- pending reboot evidence
- installed software inventory

## Safety

The collector is read-only.

It does not:

- change endpoint configuration
- enable or disable security controls
- collect credentials
- store secrets
- remediate findings

## Backend

New endpoints:

- GET /api/endpoint/sample-evidence
- GET /api/endpoint/sample-findings
- POST /api/endpoint/analyze

## Initial Finding Rules

- Secure Boot not confirmed
- TPM not ready
- BitLocker not confirmed on
- Defender not healthy
- Windows Firewall profile disabled
- RDP enabled
- SMBv1 enabled
- Pending reboot

## Status

Foundation implementation added.