from collections import Counter
from typing import Any

from app.schemas.windows_event import WindowsEventEvidence, WindowsEventRecord


SERVICE_FAILURE_EVENT_IDS = {7000, 7009, 7011, 7022, 7023, 7024, 7026, 7031, 7034, 7043}
APPLICATION_ERROR_EVENT_IDS = {1000, 1001, 1026}
DNS_CLIENT_EVENT_IDS = {1014}
SECURITY_FAILED_LOGON_EVENT_IDS = {4625}
REBOOT_EVENT_IDS = {12, 41, 1074, 6005, 6006, 6008}
WINDOWS_UPDATE_EVENT_IDS = {19, 20, 21}


def analyze_windows_event_evidence(evidence: WindowsEventEvidence) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    events = evidence.events

    _add_service_crash_findings(findings, evidence, events)
    _add_failed_logon_findings(findings, evidence, events)
    _add_application_error_findings(findings, evidence, events)
    _add_dns_client_findings(findings, evidence, events)
    _add_reboot_update_findings(findings, evidence, events)

    return findings


def _add_service_crash_findings(findings: list[dict[str, Any]], evidence: WindowsEventEvidence, events: list[WindowsEventRecord]) -> None:
    matches = [event for event in events if _is_service_failure_event(event)]

    if not matches:
        return

    findings.append(_finding(
        finding_id="WIN_EVT_SERVICE_FAILURES",
        title="Windows events contain service failure evidence",
        severity="high",
        confidence="medium",
        category="Windows service reliability",
        affected_asset=_top_computer(matches, evidence.source_file),
        evidence_items=[
            ("source_file", evidence.source_file),
            ("matching_policy", "provider-aware service control matching"),
            ("event_count", str(len(matches))),
            ("event_ids", _event_id_summary(matches)),
            ("examples", _examples(matches)),
        ],
        why_it_matters="Service crashes or startup failures can explain application outages, endpoint instability, print issues, monitoring gaps, or dependency failures.",
        safe_next_steps=[
            "Identify the affected service name and first failing timestamp.",
            "Check whether failures correlate with deployments, reboots, updates, or dependency outages.",
            "Validate service recovery settings and related application logs before restarting services.",
        ],
        limitations=[
            "Windows Event evidence may show symptoms without full root cause.",
            "Service events should be correlated with application logs and change history.",
            "Provider-aware matching reduces noise but does not replace manual service-owner validation.",
        ],
        non_actions=[
            "Do not restart production services blindly without checking active work and ownership.",
        ],
    ))


def _add_failed_logon_findings(findings: list[dict[str, Any]], evidence: WindowsEventEvidence, events: list[WindowsEventRecord]) -> None:
    matches = [event for event in events if _is_failed_logon_event(event)]

    if not matches:
        return

    findings.append(_finding(
        finding_id="WIN_EVT_FAILED_LOGONS",
        title="Windows events contain failed logon evidence",
        severity="high",
        confidence="medium",
        category="Windows access evidence",
        affected_asset=_top_computer(matches, evidence.source_file),
        evidence_items=[
            ("source_file", evidence.source_file),
            ("matching_policy", "provider-aware security log matching"),
            ("failed_logon_count", str(len(matches))),
            ("event_ids", _event_id_summary(matches)),
            ("examples", _examples(matches)),
        ],
        why_it_matters="Failed logon events can indicate wrong credentials, broken service accounts, lockout risk, misconfigured integrations, or suspicious authentication attempts.",
        safe_next_steps=[
            "Identify the account, source host, and logon type if present in the event message.",
            "Check whether the failures are expected, repeated, or linked to a service account.",
            "Correlate with account lockout, endpoint, and identity evidence.",
        ],
        limitations=[
            "Event 4625 alone does not prove malicious activity.",
            "The imported or collected evidence may not include all security event fields.",
        ],
        non_actions=[
            "Do not disable accounts or change passwords without confirming owner and business impact.",
        ],
    ))


def _add_application_error_findings(findings: list[dict[str, Any]], evidence: WindowsEventEvidence, events: list[WindowsEventRecord]) -> None:
    matches = [event for event in events if _is_application_error_event(event)]

    if not matches:
        return

    findings.append(_finding(
        finding_id="WIN_EVT_APPLICATION_ERRORS",
        title="Windows events contain application error evidence",
        severity="medium",
        confidence="medium",
        category="Application runtime evidence",
        affected_asset=_top_computer(matches, evidence.source_file),
        evidence_items=[
            ("source_file", evidence.source_file),
            ("matching_policy", "provider-aware application error matching"),
            ("application_error_count", str(len(matches))),
            ("event_ids", _event_id_summary(matches)),
            ("examples", _examples(matches)),
        ],
        why_it_matters="Application Error, Windows Error Reporting, or .NET Runtime events can explain user-facing crashes and service instability.",
        safe_next_steps=[
            "Identify the faulting application, module, and first failure timestamp.",
            "Compare the event timestamp with application logs, deployments, and endpoint changes.",
            "Check whether the error repeats across one host or multiple hosts.",
        ],
        limitations=[
            "Windows Event records may not include the complete stack trace or application context.",
        ],
        non_actions=[
            "Do not reinstall or patch applications before confirming the affected version and ownership.",
        ],
    ))


def _add_dns_client_findings(findings: list[dict[str, Any]], evidence: WindowsEventEvidence, events: list[WindowsEventRecord]) -> None:
    matches = [event for event in events if _is_dns_client_event(event)]

    if not matches:
        return

    findings.append(_finding(
        finding_id="WIN_EVT_DNS_CLIENT_ERRORS",
        title="Windows events contain DNS client resolution evidence",
        severity="medium",
        confidence="medium",
        category="Windows network dependency",
        affected_asset=_top_computer(matches, evidence.source_file),
        evidence_items=[
            ("source_file", evidence.source_file),
            ("matching_policy", "provider-aware DNS Client matching"),
            ("dns_event_count", str(len(matches))),
            ("event_ids", _event_id_summary(matches)),
            ("examples", _examples(matches)),
        ],
        why_it_matters="DNS Client events can explain application failures, logon delays, update failures, or dependency connectivity issues.",
        safe_next_steps=[
            "Extract the unresolved hostname from the event message.",
            "Validate DNS resolution from the affected host and network context.",
            "Compare with CustosOps DNS Hygiene evidence if available.",
        ],
        limitations=[
            "A DNS client event does not prove the authoritative DNS record is wrong.",
        ],
        non_actions=[
            "Do not modify DNS records without confirming ownership and expected resolution.",
        ],
    ))


def _add_reboot_update_findings(findings: list[dict[str, Any]], evidence: WindowsEventEvidence, events: list[WindowsEventRecord]) -> None:
    matches = [event for event in events if _is_reboot_or_update_event(event)]

    if not matches:
        return

    findings.append(_finding(
        finding_id="WIN_EVT_REBOOT_UPDATE_SIGNALS",
        title="Windows events contain reboot, shutdown, or update signals",
        severity="low",
        confidence="medium",
        category="Windows operational timeline",
        affected_asset=_top_computer(matches, evidence.source_file),
        evidence_items=[
            ("source_file", evidence.source_file),
            ("matching_policy", "provider-aware operational timeline matching"),
            ("signal_count", str(len(matches))),
            ("event_ids", _event_id_summary(matches)),
            ("examples", _examples(matches)),
        ],
        why_it_matters="Reboot, shutdown, or update events help build an operational timeline around incidents, outages, or patch-related changes.",
        safe_next_steps=[
            "Use these timestamps to correlate with service failures, application errors, and user impact.",
            "Check whether reboot or update activity was planned.",
        ],
        limitations=[
            "These events are usually timeline evidence, not root cause by themselves.",
        ],
        non_actions=[
            "Do not treat reboot evidence as a security finding without additional context.",
        ],
    ))


def _is_service_failure_event(event: WindowsEventRecord) -> bool:
    if not _is_service_control_manager_event(event):
        return False

    if event.event_id in SERVICE_FAILURE_EVENT_IDS:
        return True

    return _contains_any(
        event.message,
        [
            "terminated unexpectedly",
            "failed to start",
            "service did not respond",
            "service terminated",
            "service failed",
            "dependent service",
        ],
    )


def _is_failed_logon_event(event: WindowsEventRecord) -> bool:
    if not _is_security_event(event):
        return False

    if event.event_id in SECURITY_FAILED_LOGON_EVENT_IDS:
        return True

    return _contains_any(event.message, ["failed logon", "an account failed to log on", "audit failure"])


def _is_application_error_event(event: WindowsEventRecord) -> bool:
    if _is_application_error_provider(event):
        if event.event_id in APPLICATION_ERROR_EVENT_IDS:
            return True
        return _contains_any(event.message, ["faulting application", "exception", "crash", "fault bucket"])

    if not _is_application_log_event(event):
        return False

    if event.event_id in APPLICATION_ERROR_EVENT_IDS:
        return True

    return _contains(event.level, "error") and _contains_any(
        event.message,
        ["faulting application", "exception", "crash", "fault bucket"],
    )


def _is_dns_client_event(event: WindowsEventRecord) -> bool:
    if not _is_dns_client_context(event):
        return False

    if event.event_id in DNS_CLIENT_EVENT_IDS:
        return True

    return _contains_any(event.message, ["name resolution for the name", "dns query", "name resolution timed out"])


def _is_reboot_or_update_event(event: WindowsEventRecord) -> bool:
    if event.event_id in WINDOWS_UPDATE_EVENT_IDS:
        return _is_windows_update_context(event)

    if event.event_id in REBOOT_EVENT_IDS:
        return _is_system_timeline_context(event)

    return _is_system_timeline_context(event) and _contains_any(
        event.message,
        ["restart", "reboot", "shutdown", "windows update", "unexpected shutdown"],
    )


def _is_service_control_manager_event(event: WindowsEventRecord) -> bool:
    return _contains(event.provider, "service control manager")


def _is_security_event(event: WindowsEventRecord) -> bool:
    return _contains(event.provider, "security-auditing") or _equals(event.log_name, "security")


def _is_application_error_provider(event: WindowsEventRecord) -> bool:
    return _contains_any(event.provider, ["application error", ".net runtime", "windows error reporting"])


def _is_application_log_event(event: WindowsEventRecord) -> bool:
    return _equals(event.log_name, "application") or _is_application_error_provider(event)


def _is_dns_client_context(event: WindowsEventRecord) -> bool:
    return _contains(event.provider, "dns-client") or _contains(event.provider, "dns client") or _contains(event.log_name, "dns-client")


def _is_windows_update_context(event: WindowsEventRecord) -> bool:
    return _contains(event.provider, "windowsupdateclient") or _contains(event.provider, "windows update") or _contains(event.log_name, "windowsupdateclient")


def _is_system_timeline_context(event: WindowsEventRecord) -> bool:
    return (
        _equals(event.log_name, "system")
        or _contains_any(event.provider, ["user32", "eventlog", "kernel-power", "kernel-general", "windowsupdateclient"])
        or _is_windows_update_context(event)
    )


def _finding(
    finding_id: str,
    title: str,
    severity: str,
    confidence: str,
    category: str,
    affected_asset: str,
    evidence_items: list[tuple[str, str]],
    why_it_matters: str,
    safe_next_steps: list[str],
    limitations: list[str],
    non_actions: list[str],
) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "title": title,
        "severity": severity,
        "confidence": confidence,
        "category": category,
        "affected_asset": affected_asset,
        "evidence": [
            {"source": "windows_event_log", "key": key, "value": value}
            for key, value in evidence_items
        ],
        "why_it_matters": why_it_matters,
        "safe_next_steps": safe_next_steps,
        "limitations": limitations,
        "non_actions": non_actions,
        "status": "open",
    }


def _contains(value: str | None, needle: str) -> bool:
    return needle.lower() in str(value or "").lower()


def _contains_any(value: str | None, needles: list[str]) -> bool:
    haystack = str(value or "").lower()
    return any(needle.lower() in haystack for needle in needles)


def _equals(value: str | None, expected: str) -> bool:
    return str(value or "").lower() == expected.lower()


def _top_computer(events: list[WindowsEventRecord], fallback: str) -> str:
    computers = [event.computer for event in events if event.computer]

    if not computers:
        return fallback

    return Counter(computers).most_common(1)[0][0]


def _event_id_summary(events: list[WindowsEventRecord]) -> str:
    counter = Counter(str(event.event_id or "unknown") for event in events)
    return ", ".join(f"{event_id}: {count}" for event_id, count in counter.most_common())


def _examples(events: list[WindowsEventRecord], limit: int = 3) -> str:
    examples: list[str] = []

    for event in events[:limit]:
        timestamp = event.timestamp or "unknown-time"
        event_id = event.event_id or "unknown-id"
        provider = event.provider or "unknown-provider"
        message = event.message[:180].replace("\n", " ")
        examples.append(f"{timestamp} event_id={event_id} provider={provider} message={message}")

    return " | ".join(examples)
