import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_LOG_SAMPLE = PROJECT_ROOT / "samples" / "app_logs" / "fastapi-api-errors.log"


def test_endpoint_report_infers_endpoint_name_from_findings_when_evidence_is_session_fallback():
    response = client.post(
        "/api/reports/endpoint",
        json={
            "evidence": {
                "source_type": "endpoint_session_evidence",
                "generated_from": "loaded findings",
                "source_file": "custosops-session",
            },
            "findings": [
                {
                    "finding_id": "ENDPOINT_SECURE_BOOT_NOT_CONFIRMED",
                    "title": "Secure Boot is not confirmed as enabled",
                    "severity": "high",
                    "confidence": "medium",
                    "category": "Endpoint security baseline",
                    "affected_asset": "LAB-WIN11-01",
                    "evidence": [{"source": "endpoint", "key": "secure_boot", "value": "disabled"}],
                    "why_it_matters": "Secure Boot matters.",
                    "safe_next_steps": ["Validate firmware and policy."],
                    "limitations": ["Some VMs may not support Secure Boot."],
                    "non_actions": ["Do not change firmware without approval."],
                }
            ],
            "format": "html",
            "archive": False,
        },
    )

    assert response.status_code == 200
    content = response.json()["content"]

    assert "LAB-WIN11-01" in content
    assert "unknown-endpoint" not in content
    assert "Restored session evidence" in content


def test_dns_report_derives_record_count_from_findings_when_raw_records_are_missing():
    response = client.post(
        "/api/reports/dns",
        json={
            "evidence": {
                "source_type": "dns_session_evidence",
                "generated_from": "loaded findings",
                "source_file": "custosops-session",
            },
            "findings": [
                {
                    "finding_id": "DNS_PTR_NOT_HEALTHY",
                    "title": "Reverse DNS is missing or inconsistent",
                    "severity": "medium",
                    "confidence": "medium",
                    "category": "DNS hygiene",
                    "affected_asset": "app-old.lab.local",
                    "evidence": [{"source": "dns", "key": "ptr_status", "value": "NO_PTR"}],
                    "why_it_matters": "Reverse DNS matters.",
                    "safe_next_steps": ["Validate PTR ownership."],
                    "limitations": ["PTR may not be required."],
                    "non_actions": ["Do not modify DNS without ownership."],
                },
                {
                    "finding_id": "DNS_FORWARD_NOT_OK",
                    "title": "DNS forward resolution is not confirmed healthy",
                    "severity": "medium",
                    "confidence": "medium",
                    "category": "DNS hygiene",
                    "affected_asset": "legacy-alias-01.lab.local",
                    "evidence": [{"source": "dns", "key": "forward_status", "value": "FORWARD_MISMATCH"}],
                    "why_it_matters": "Forward DNS matters.",
                    "safe_next_steps": ["Validate forward DNS."],
                    "limitations": ["Evidence may be stale."],
                    "non_actions": ["Do not modify DNS without ownership."],
                },
            ],
            "format": "json",
            "archive": False,
        },
    )

    assert response.status_code == 200
    payload = json.loads(response.json()["content"])

    assert payload["summary"]["record_count"] == 2
    assert payload["summary"]["record_count_is_derived"] is True
    assert payload["summary"]["source_label"] == "Restored session evidence"


def test_app_log_html_report_is_real_html_not_markdown_wrapped_in_paragraphs():
    import_response = client.post(
        "/api/app-log/import",
        json={
            "filename": APP_LOG_SAMPLE.name,
            "content": APP_LOG_SAMPLE.read_text(encoding="utf-8-sig"),
        },
    )

    assert import_response.status_code == 200
    imported = import_response.json()

    report_response = client.post(
        "/api/reports/app-log",
        json={
            "evidence": imported["evidence"],
            "findings": imported["findings"],
            "format": "html",
            "archive": False,
        },
    )

    assert report_response.status_code == 200

    content = report_response.json()["content"]

    assert "<h1>Application Log Evidence Report</h1>" in content
    assert "<p># CustosOps Application Log Evidence Report</p>" not in content
    assert "Sensitive Evidence Warning" in content