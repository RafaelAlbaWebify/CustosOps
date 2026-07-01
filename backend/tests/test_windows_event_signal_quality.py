from app.analyzers.windows_event_evidence import analyze_windows_event_evidence
from app.schemas.windows_event import WindowsEventEvidence, WindowsEventRecord


def _event(provider: str, event_id: int, message: str, log_name: str = "System") -> WindowsEventRecord:
    return WindowsEventRecord(
        record_number=1,
        timestamp="2026-07-01T10:00:00+02:00",
        provider=provider,
        event_id=event_id,
        level="Error",
        computer="TRON",
        log_name=log_name,
        message=message,
        raw={},
    )


def _evidence(events: list[WindowsEventRecord]) -> WindowsEventEvidence:
    return WindowsEventEvidence(
        source_file="quality-test",
        source_type="windows_event_log_local_collection",
        raw_event_count=len(events),
        parsed_event_count=len(events),
        events=events,
        parser_warnings=[],
    )


def test_service_failure_matching_ignores_winlogon_7001_noise():
    evidence = _evidence(
        [
            _event(
                provider="Service Control Manager",
                event_id=7000,
                message="The Google Updater Service service failed to start due to timeout.",
            ),
            _event(
                provider="Microsoft-Windows-Winlogon",
                event_id=7001,
                message="User Log-on Notification for Customer Experience Improvement Program",
            ),
            _event(
                provider="Microsoft-Windows-Winlogon",
                event_id=7001,
                message="User Log-on Notification for Customer Experience Improvement Program",
            ),
        ]
    )

    findings = analyze_windows_event_evidence(evidence)
    service = next(finding for finding in findings if finding["finding_id"] == "WIN_EVT_SERVICE_FAILURES")
    evidence_items = {item["key"]: item["value"] for item in service["evidence"]}

    assert evidence_items["event_count"] == "1"
    assert evidence_items["event_ids"] == "7000: 1"
    assert "Winlogon" not in evidence_items["examples"]
    assert evidence_items["matching_policy"] == "provider-aware service control matching"


def test_event_id_alone_does_not_create_failed_logon_without_security_context():
    evidence = _evidence(
        [
            _event(
                provider="Example-App",
                event_id=4625,
                message="Application-specific code 4625, not a Windows failed logon event.",
                log_name="Application",
            )
        ]
    )

    findings = analyze_windows_event_evidence(evidence)
    finding_ids = {finding["finding_id"] for finding in findings}

    assert "WIN_EVT_FAILED_LOGONS" not in finding_ids


def test_dns_event_id_requires_dns_client_context():
    evidence = _evidence(
        [
            _event(
                provider="Example-App",
                event_id=1014,
                message="Application-specific code 1014, not DNS Client.",
                log_name="Application",
            )
        ]
    )

    findings = analyze_windows_event_evidence(evidence)
    finding_ids = {finding["finding_id"] for finding in findings}

    assert "WIN_EVT_DNS_CLIENT_ERRORS" not in finding_ids
