from typing import Any

from app.schemas.endpoint import EndpointEvidence
from app.schemas.finding import EvidenceItem, SecurityFinding


def _asset_name(evidence: EndpointEvidence) -> str:
    return str(evidence.computer.get("computer_name") or "unknown-endpoint")


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        if value == 1:
            return True
        if value == 0:
            return False

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "enabled", "on", "1"}:
            return True
        if lowered in {"false", "no", "disabled", "off", "0"}:
            return False

    return None


def _evidence(source: str, key: str, value: Any) -> EvidenceItem:
    return EvidenceItem(source=source, key=key, value=str(value))


def analyze_endpoint_evidence(evidence: EndpointEvidence) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    asset = _asset_name(evidence)

    firmware = evidence.firmware
    encryption = evidence.encryption
    protection = evidence.protection
    access_surface = evidence.access_surface
    maintenance = evidence.maintenance

    secure_boot = str(firmware.get("secure_boot", "unknown")).lower()
    if secure_boot not in {"enabled", "true"}:
        findings.append(
            SecurityFinding(
                finding_id="ENDPOINT_SECURE_BOOT_NOT_CONFIRMED",
                title="Secure Boot is not confirmed as enabled",
                severity="medium" if secure_boot.startswith("unknown") else "high",
                confidence="medium",
                category="Endpoint security baseline",
                affected_asset=asset,
                evidence=[_evidence("firmware", "secure_boot", secure_boot)],
                why_it_matters=(
                    "Secure Boot helps reduce the risk of unauthorized boot components "
                    "or boot-level tampering. If it is disabled or unsupported, the endpoint "
                    "may not meet common security baseline expectations."
                ),
                limitations=[
                    "Some virtual machines and older systems may not support Secure Boot.",
                    "This finding should be validated against the organization's endpoint baseline.",
                ],
                safe_next_steps=[
                    "Confirm whether this device model and firmware support Secure Boot.",
                    "Check whether Secure Boot is required by policy or compliance controls.",
                    "Escalate to endpoint administration before changing firmware settings.",
                ],
                non_actions=[
                    "Do not change firmware settings without approval.",
                    "Do not assume compromise from this evidence alone.",
                ],
            )
        )

    tpm = firmware.get("tpm", {})
    tpm_present = _as_bool(tpm.get("Present")) if isinstance(tpm, dict) else None
    tpm_ready = _as_bool(tpm.get("Ready")) if isinstance(tpm, dict) else None
    if tpm_present is not True or tpm_ready is not True:
        findings.append(
            SecurityFinding(
                finding_id="ENDPOINT_TPM_NOT_READY",
                title="TPM is not confirmed as present and ready",
                severity="medium",
                confidence="medium",
                category="Endpoint security baseline",
                affected_asset=asset,
                evidence=[
                    _evidence("firmware", "tpm_present", tpm.get("Present", "unknown") if isinstance(tpm, dict) else "unknown"),
                    _evidence("firmware", "tpm_ready", tpm.get("Ready", "unknown") if isinstance(tpm, dict) else "unknown"),
                ],
                why_it_matters=(
                    "TPM readiness is commonly required for BitLocker, device trust, "
                    "and modern Windows security baselines."
                ),
                limitations=[
                    "TPM status can be unavailable depending on permissions, hardware, firmware, or VM type.",
                ],
                safe_next_steps=[
                    "Validate TPM state locally or through endpoint management.",
                    "Check whether the endpoint should support TPM-based controls.",
                ],
                non_actions=[
                    "Do not clear or reset TPM without a recovery and change-control plan.",
                ],
            )
        )

    bitlocker = encryption.get("bitlocker", {})
    protection_status = str(bitlocker.get("ProtectionStatus", "unknown")).lower() if isinstance(bitlocker, dict) else "unknown"
    if protection_status not in {"on", "1"}:
        findings.append(
            SecurityFinding(
                finding_id="ENDPOINT_BITLOCKER_NOT_CONFIRMED_ON",
                title="BitLocker protection is not confirmed as on",
                severity="high",
                confidence="medium",
                category="Endpoint encryption",
                affected_asset=asset,
                evidence=[
                    _evidence("encryption", "bitlocker_protection_status", protection_status),
                    _evidence("encryption", "bitlocker_volume_status", bitlocker.get("VolumeStatus", "unknown") if isinstance(bitlocker, dict) else "unknown"),
                ],
                why_it_matters=(
                    "Disk encryption helps protect data if the endpoint is lost, stolen, "
                    "or removed from controlled facilities."
                ),
                limitations=[
                    "Some editions or environments may report BitLocker differently.",
                    "The result should be compared with endpoint management or recovery key records.",
                ],
                safe_next_steps=[
                    "Confirm the expected encryption policy for this endpoint.",
                    "Check whether a recovery key exists before any remediation.",
                    "Escalate through the normal endpoint security workflow.",
                ],
                non_actions=[
                    "Do not enable encryption without confirming recovery key handling.",
                ],
            )
        )

    defender = protection.get("defender", {})
    av_enabled = _as_bool(defender.get("AntivirusEnabled")) if isinstance(defender, dict) else None
    realtime_enabled = _as_bool(defender.get("RealTimeProtection")) if isinstance(defender, dict) else None
    if av_enabled is not True or realtime_enabled is not True:
        findings.append(
            SecurityFinding(
                finding_id="ENDPOINT_DEFENDER_NOT_HEALTHY",
                title="Microsoft Defender antivirus or real-time protection is not confirmed healthy",
                severity="high",
                confidence="medium",
                category="Endpoint protection",
                affected_asset=asset,
                evidence=[
                    _evidence("protection", "antivirus_enabled", defender.get("AntivirusEnabled", "unknown") if isinstance(defender, dict) else "unknown"),
                    _evidence("protection", "real_time_protection", defender.get("RealTimeProtection", "unknown") if isinstance(defender, dict) else "unknown"),
                ],
                why_it_matters=(
                    "Endpoint protection and real-time scanning are basic controls for reducing "
                    "malware and suspicious activity risk."
                ),
                limitations=[
                    "This check may be unavailable if Defender cmdlets are blocked or another AV product is active.",
                    "A third-party EDR/AV may be expected in some environments.",
                ],
                safe_next_steps=[
                    "Validate endpoint protection status in the approved management console.",
                    "Confirm whether Defender or another security product is the expected control.",
                ],
                non_actions=[
                    "Do not remove or change security products without approval.",
                ],
            )
        )

    firewall_profiles = protection.get("firewall_profiles", [])
    if isinstance(firewall_profiles, list) and firewall_profiles:
        disabled_profiles = [
            str(profile.get("Name", "unknown"))
            for profile in firewall_profiles
            if isinstance(profile, dict) and _as_bool(profile.get("Enabled")) is not True
        ]
        if disabled_profiles:
            findings.append(
                SecurityFinding(
                    finding_id="ENDPOINT_FIREWALL_PROFILE_DISABLED",
                    title="One or more Windows Firewall profiles are disabled",
                    severity="medium",
                    confidence="high",
                    category="Endpoint network protection",
                    affected_asset=asset,
                    evidence=[_evidence("protection", "disabled_firewall_profiles", ", ".join(disabled_profiles))],
                    why_it_matters=(
                        "Host firewall profiles reduce unnecessary inbound exposure and are "
                        "a common endpoint baseline control."
                    ),
                    limitations=[
                        "Some environments manage firewall posture through third-party controls.",
                    ],
                    safe_next_steps=[
                        "Confirm expected firewall policy for domain, private, and public profiles.",
                        "Validate whether a management policy intentionally controls this setting.",
                    ],
                    non_actions=[
                        "Do not enable firewall profiles without checking application impact.",
                    ],
                )
            )

    rdp = access_surface.get("rdp", {})
    rdp_enabled = _as_bool(rdp.get("Enabled")) if isinstance(rdp, dict) else None
    if rdp_enabled is True:
        findings.append(
            SecurityFinding(
                finding_id="ENDPOINT_RDP_ENABLED",
                title="Remote Desktop is enabled",
                severity="medium",
                confidence="high",
                category="Endpoint exposure",
                affected_asset=asset,
                evidence=[_evidence("access_surface", "rdp_enabled", True)],
                why_it_matters=(
                    "RDP increases the endpoint access surface and should be justified, "
                    "restricted, monitored, and protected by policy."
                ),
                limitations=[
                    "RDP may be valid for managed admin workflows.",
                    "Network exposure and firewall rules were not fully validated by this check.",
                ],
                safe_next_steps=[
                    "Confirm whether RDP is required on this endpoint.",
                    "Validate access restrictions, firewall scope, and administrative ownership.",
                ],
                non_actions=[
                    "Do not disable RDP if it is required for approved support workflows without coordination.",
                ],
            )
        )

    smbv1 = access_surface.get("smbv1", {})
    smbv1_enabled = _as_bool(smbv1.get("EnableSMB1Protocol")) if isinstance(smbv1, dict) else None
    if smbv1_enabled is True:
        findings.append(
            SecurityFinding(
                finding_id="ENDPOINT_SMBV1_ENABLED",
                title="SMBv1 is enabled",
                severity="high",
                confidence="high",
                category="Endpoint exposure",
                affected_asset=asset,
                evidence=[_evidence("access_surface", "smbv1_enabled", True)],
                why_it_matters=(
                    "SMBv1 is an outdated protocol and is generally discouraged because of "
                    "security and resilience concerns."
                ),
                limitations=[
                    "Legacy applications or devices may still depend on SMBv1 in some environments.",
                ],
                safe_next_steps=[
                    "Identify whether any approved legacy dependency requires SMBv1.",
                    "Plan disablement through change control if no dependency exists.",
                ],
                non_actions=[
                    "Do not disable SMBv1 without validating legacy application impact.",
                ],
            )
        )

    pending_reboot = maintenance.get("pending_reboot", {})
    pending = _as_bool(pending_reboot.get("IsPending")) if isinstance(pending_reboot, dict) else None
    if pending is True:
        findings.append(
            SecurityFinding(
                finding_id="ENDPOINT_PENDING_REBOOT",
                title="Endpoint has pending reboot evidence",
                severity="low",
                confidence="medium",
                category="Maintenance hygiene",
                affected_asset=asset,
                evidence=[_evidence("maintenance", "pending_reboot", True)],
                why_it_matters=(
                    "Pending reboot state can delay patch completion, security baseline application, "
                    "or endpoint management policy convergence."
                ),
                limitations=[
                    "Pending reboot evidence does not prove a security patch is missing by itself.",
                ],
                safe_next_steps=[
                    "Coordinate a reboot window if the endpoint is production-sensitive.",
                    "Recheck security posture after reboot.",
                ],
                non_actions=[
                    "Do not reboot production-critical endpoints without approval.",
                ],
            )
        )

    if not findings:
        findings.append(
            SecurityFinding(
                finding_id="ENDPOINT_BASELINE_NO_MAJOR_FINDINGS",
                title="No major endpoint baseline findings in current evidence",
                severity="info",
                confidence="medium",
                category="Endpoint security baseline",
                affected_asset=asset,
                evidence=[_evidence("endpoint", "analysis_result", "no_major_findings")],
                why_it_matters=(
                    "The current evidence did not trigger the initial CustosOps endpoint rules."
                ),
                limitations=[
                    "This is not a full vulnerability assessment.",
                    "Patch status, EDR telemetry, policy compliance, and exposure context are not complete yet.",
                ],
                safe_next_steps=[
                    "Continue with DNS, identity, M365, and vulnerability prioritization modules.",
                ],
                non_actions=[
                    "Do not treat this as proof of complete security compliance.",
                ],
            )
        )

    return findings