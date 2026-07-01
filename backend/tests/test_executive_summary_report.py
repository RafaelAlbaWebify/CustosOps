from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _finding(finding_id: str, title: str, severity: str, module_asset: str, status: str = "open") -> dict:
    return {
        "finding_id": finding_id,
        "title": title,
        "severity": severity,
        "confidence": "medium",
        "category": "Test evidence",
        "affected_asset": module_asset,
        "evidence": [{"source": "test", "key": "example", "value": "present"}],
        "why_it_matters": "This finding is included in executive summary testing.",
        "safe_next_steps": ["Validate the finding and assign an owner."],
        "limitations": ["This is test evidence."],
        "non_actions": ["Do not remediate from this test."],
        "status": status,
        "review_notes": "Reviewed in test." if status == "reviewed" else None,
        "reviewed_by": "local-operator" if status == "reviewed" else None,
        "reviewed_at": "2026-07-01T10:00:00Z" if status == "reviewed" else None,
    }


def test_executive_summary_html_report_combines_modules():
    response = client.post(
        "/api/reports/executive-summary",
        json={
            "format": "html",
            "archive": False,
            "modules": [
                {
                    "module_id": "endpoint",
                    "module_name": "Endpoint Security",
                    "source": "LAB-WIN11-01",
                    "evidence": {"endpoint_name": "LAB-WIN11-01"},
                    "findings": [
                        _finding("ENDPOINT_TEST_HIGH", "Endpoint high risk", "high", "LAB-WIN11-01", "reviewed")
                    ],
                },
                {
                    "module_id": "dns",
                    "module_name": "DNS Hygiene",
                    "source": "dns-audit.csv",
                    "evidence": {"records": [{"host_name": "app-old.lab.local"}]},
                    "findings": [
                        _finding("DNS_TEST_MEDIUM", "DNS medium risk", "medium", "app-old.lab.local")
                    ],
                },
                {
                    "module_id": "app-log",
                    "module_name": "Application Logs",
                    "source": "app.log",
                    "evidence": {"parsed_entry_count": 10},
                    "findings": [
                        _finding("APP_TEST_HIGH", "Application high risk", "high", "/api/orders")
                    ],
                },
                {
                    "module_id": "windows-events",
                    "module_name": "Windows Event Evidence",
                    "source": "events.json",
                    "evidence": {"parsed_event_count": 6},
                    "findings": [
                        _finding("WIN_EVT_TEST_LOW", "Windows event low risk", "low", "LAB-WIN11-01")
                    ],
                },
            ],
        },
    )

    assert response.status_code == 200
    data = response.json()
    content = data["content"]

    assert data["filename"].startswith("custosops_executive_summary_")
    assert "Operational Evidence Summary" in content
    assert "Endpoint Security" in content
    assert "DNS Hygiene" in content
    assert "Application Logs" in content
    assert "Windows Event Evidence" in content
    assert "Endpoint high risk" in content
    assert "Review Status" in content
    assert "Reviewed" in content


def test_executive_summary_json_report_has_stable_type_and_counts():
    response = client.post(
        "/api/reports/executive-summary",
        json={
            "format": "json",
            "archive": False,
            "modules": [
                {
                    "module_id": "endpoint",
                    "module_name": "Endpoint Security",
                    "source": "LAB-WIN11-01",
                    "evidence": {"endpoint_name": "LAB-WIN11-01"},
                    "findings": [
                        _finding("ENDPOINT_TEST_HIGH", "Endpoint high risk", "high", "LAB-WIN11-01")
                    ],
                }
            ],
        },
    )

    assert response.status_code == 200
    content = response.json()["content"]

    assert '"report_type": "custosops.executive_summary.v0.1"' in content
    assert '"finding_count": 1' in content
    assert '"high": 1' in content
