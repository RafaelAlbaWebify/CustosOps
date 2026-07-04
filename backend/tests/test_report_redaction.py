import json

from fastapi.testclient import TestClient

from app.main import app
from app.services import redaction_settings


client = TestClient(app)


def test_app_log_json_report_applies_default_redaction_settings(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"

    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_DIR", tmp_path)
    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_PATH", settings_path)

    reset_response = client.post("/api/redaction/settings/reset")
    assert reset_response.status_code == 200

    response = client.post(
        "/api/reports/app-log",
        json={
            "evidence": {
                "source_file": "C:\\Users\\analyst\\logs\\app.log",
                "raw_line_count": 1,
                "parsed_entry_count": 1,
                "entries": [
                    {
                        "message": "Contact analyst@example.com from C:\\Users\\analyst\\Desktop",
                    }
                ],
            },
            "findings": [
                {
                    "finding_id": "APP_LOG_REDACTION_TEST",
                    "title": "Sensitive application log evidence",
                    "severity": "medium",
                    "confidence": "medium",
                    "category": "Application logs",
                    "affected_asset": "app01",
                    "evidence": [
                        {
                            "source": "app-log",
                            "key": "message",
                            "value": "Contact analyst@example.com from C:\\Users\\analyst\\Desktop",
                        }
                    ],
                    "why_it_matters": "The report should not expose analyst@example.com.",
                    "safe_next_steps": ["Review C:\\Users\\analyst\\Desktop safely."],
                    "limitations": ["Synthetic test."],
                    "non_actions": ["Do not remediate."],
                }
            ],
            "format": "json",
            "archive": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["redaction"]["enabled"] is True
    assert data["redaction"]["changed"] is True
    assert "email-addresses" in data["redaction"]["applied_rules"]
    assert "user-profile-paths" in data["redaction"]["applied_rules"]

    content = data["content"]

    assert "analyst@example.com" not in content
    assert "C:\\Users\\analyst" not in content
    assert "[REDACTED_EMAIL]" in content
    assert "[REDACTED_USER]" in content

    parsed = json.loads(content)
    assert parsed["report_type"] == "custosops.app_log.v0.1"


def test_executive_summary_html_report_applies_redaction_to_rendered_fields(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"

    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_DIR", tmp_path)
    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_PATH", settings_path)

    reset_response = client.post("/api/redaction/settings/reset")
    assert reset_response.status_code == 200

    response = client.post(
        "/api/reports/executive-summary",
        json={
            "modules": [
                {
                    "module_id": "app-logs",
                    "module_name": "Application Logs",
                    "source": "Contact analyst@example.com from C:\\Users\\analyst\\logs\\app.log",
                    "evidence": {
                        "source_file": "Contact analyst@example.com from C:\\Users\\analyst\\logs\\app.log",
                    },
                    "findings": [
                        {
                            "finding_id": "EXEC_REDACTION_TEST",
                            "title": "Sensitive executive summary evidence",
                            "severity": "high",
                            "confidence": "medium",
                            "category": "Application logs",
                            "affected_asset": "app01",
                            "evidence": [
                                {
                                    "source": "app-log",
                                    "key": "message",
                                    "value": "Contact analyst@example.com from C:\\Users\\analyst\\Desktop",
                                }
                            ],
                            "why_it_matters": "Contact analyst@example.com from C:\\Users\\analyst\\Desktop",
                            "safe_next_steps": ["Review C:\\Users\\analyst\\Desktop safely."],
                            "limitations": ["Synthetic test."],
                            "non_actions": ["Do not remediate."],
                        }
                    ],
                }
            ],
            "format": "html",
            "archive": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    content = data["content"]

    assert data["redaction"]["enabled"] is True
    assert data["redaction"]["changed"] is True

    assert "analyst@example.com" not in content
    assert "C:\\Users\\analyst" not in content
    assert "[REDACTED_EMAIL]" in content
    assert "[REDACTED_USER]" in content


def test_report_redaction_can_be_disabled(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"

    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_DIR", tmp_path)
    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_PATH", settings_path)

    update_response = client.put(
        "/api/redaction/settings",
        json={
            "enabled": False,
            "profile_name": "disabled-test",
            "rules": [
                {
                    "rule_id": "email-addresses",
                    "label": "Email addresses",
                    "kind": "pattern",
                    "value": "email",
                    "enabled": True,
                    "replacement": "[EMAIL]",
                }
            ],
        },
    )
    assert update_response.status_code == 200

    response = client.post(
        "/api/reports/app-log",
        json={
            "evidence": {
                "source_file": "app.log",
                "raw_line_count": 1,
                "parsed_entry_count": 1,
            },
            "findings": [
                {
                    "finding_id": "APP_LOG_REDACTION_DISABLED_TEST",
                    "title": "Sensitive application log evidence",
                    "severity": "medium",
                    "confidence": "medium",
                    "category": "Application logs",
                    "affected_asset": "app01",
                    "evidence": [
                        {
                            "source": "app-log",
                            "key": "message",
                            "value": "Contact analyst@example.com",
                        }
                    ],
                    "why_it_matters": "Contact analyst@example.com",
                    "safe_next_steps": ["Review safely."],
                    "limitations": ["Synthetic test."],
                    "non_actions": ["Do not remediate."],
                }
            ],
            "format": "markdown",
            "archive": False,
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["redaction"]["enabled"] is False
    assert data["redaction"]["changed"] is False
    assert data["redaction"]["applied_rules"] == []
    assert "analyst@example.com" in data["content"]
