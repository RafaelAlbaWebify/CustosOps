from typing import Any

from app.schemas.iis import IisApplicationPool, IisEvidence, IisServiceStatus, IisSite


def analyze_iis_evidence(evidence: IisEvidence) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    _add_stopped_service_finding(findings, evidence)
    _add_stopped_site_finding(findings, evidence)
    _add_stopped_app_pool_finding(findings, evidence)
    _add_logging_visibility_finding(findings, evidence)

    return findings


def _add_stopped_service_finding(findings: list[dict[str, Any]], evidence: IisEvidence) -> None:
    relevant = [service for service in evidence.services if _service_is_relevant(service)]
    stopped = [service for service in relevant if not _is_running(service.status)]

    if not stopped:
        return

    findings.append(
        _finding(
            finding_id="IIS_SERVICE_NOT_RUNNING",
            title="IIS-related service is not running",
            severity="medium",
            confidence="medium",
            category="IIS service state",
            affected_asset=evidence.asset or evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("service_count", str(len(stopped))),
                ("services", _service_summary(stopped)),
            ],
            why_it_matters="Stopped IIS-related services can explain unavailable web applications, missing logs, failed health checks, or failed local IIS collection.",
            safe_next_steps=[
                "Confirm whether IIS is expected to be installed and serving applications on this host.",
                "Check the service owner and maintenance window before changing service state.",
                "Correlate with Windows Event evidence for service start or failure events.",
            ],
            limitations=[
                "A stopped service can be normal when IIS is not installed or not used on the host.",
                "This evidence is read-only and does not prove application outage by itself.",
            ],
            non_actions=["Do not start or restart IIS services automatically from CustosOps."],
        )
    )


def _add_stopped_site_finding(findings: list[dict[str, Any]], evidence: IisEvidence) -> None:
    stopped = [site for site in evidence.sites if _is_stopped(site.state)]

    if not stopped:
        return

    findings.append(
        _finding(
            finding_id="IIS_SITE_STOPPED",
            title="IIS site inventory contains stopped sites",
            severity="medium",
            confidence="medium",
            category="IIS site state",
            affected_asset=evidence.asset or evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("site_count", str(len(stopped))),
                ("sites", _site_summary(stopped)),
            ],
            why_it_matters="Stopped IIS sites can explain application unavailability even when the server itself is reachable.",
            safe_next_steps=[
                "Confirm whether each stopped site is expected to be active.",
                "Check bindings, application pool state, recent changes, and related Windows Event evidence.",
            ],
            limitations=["A stopped site can be intentional for retired or staging applications."],
            non_actions=["Do not start sites without confirming application owner and production impact."],
        )
    )


def _add_stopped_app_pool_finding(findings: list[dict[str, Any]], evidence: IisEvidence) -> None:
    stopped = [pool for pool in evidence.application_pools if _is_stopped(pool.state)]

    if not stopped:
        return

    findings.append(
        _finding(
            finding_id="IIS_APP_POOL_STOPPED",
            title="IIS application pool inventory contains stopped pools",
            severity="high",
            confidence="medium",
            category="IIS application pool state",
            affected_asset=evidence.asset or evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("app_pool_count", str(len(stopped))),
                ("application_pools", _app_pool_summary(stopped)),
            ],
            why_it_matters="Stopped application pools can make IIS applications unavailable while the site binding still appears configured.",
            safe_next_steps=[
                "Identify which applications use the stopped pool.",
                "Check application pool identity, recent crashes, rapid-fail protection, and application event logs.",
            ],
            limitations=["Application pool state alone does not identify the root cause of the stop."],
            non_actions=["Do not restart application pools blindly without checking active transactions and ownership."],
        )
    )


def _add_logging_visibility_finding(findings: list[dict[str, Any]], evidence: IisEvidence) -> None:
    if not evidence.iis_detected:
        return

    if evidence.log_files:
        return

    findings.append(
        _finding(
            finding_id="IIS_LOGS_NOT_OBSERVED",
            title="IIS appears present but no IIS log files were observed",
            severity="low",
            confidence="low",
            category="IIS evidence visibility",
            affected_asset=evidence.asset or evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("appcmd_available", str(evidence.appcmd_available)),
                ("log_directories", str(len(evidence.log_directories))),
                ("warnings", " | ".join(evidence.collection_warnings[:5])),
            ],
            why_it_matters="Missing IIS log visibility limits incident reconstruction and report confidence for web application troubleshooting.",
            safe_next_steps=[
                "Confirm whether IIS logging is enabled and where logs are written.",
                "Check whether the application is hosted elsewhere or behind another web server.",
            ],
            limitations=["No log files observed can be normal for hosts where IIS is not actively serving traffic."],
            non_actions=["Do not enable or modify IIS logging from CustosOps."],
        )
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
            {"source": "iis_application", "key": key, "value": value}
            for key, value in evidence_items
        ],
        "why_it_matters": why_it_matters,
        "safe_next_steps": safe_next_steps,
        "limitations": limitations,
        "non_actions": non_actions,
        "status": "open",
    }


def _service_is_relevant(service: IisServiceStatus) -> bool:
    return str(service.name or "").upper() in {"W3SVC", "WAS", "IISADMIN", "WEBMANAGEMENTSERVICE"}


def _is_running(value: str | None) -> bool:
    return str(value or "").lower() == "running"


def _is_stopped(value: str | None) -> bool:
    return str(value or "").lower() == "stopped"


def _service_summary(services: list[IisServiceStatus]) -> str:
    return ", ".join(f"{service.name or 'unknown'}={service.status or 'unknown'}" for service in services)


def _site_summary(sites: list[IisSite]) -> str:
    return ", ".join(f"{site.name or 'unknown'}={site.state or 'unknown'}" for site in sites)


def _app_pool_summary(pools: list[IisApplicationPool]) -> str:
    return ", ".join(f"{pool.name or 'unknown'}={pool.state or 'unknown'}" for pool in pools)