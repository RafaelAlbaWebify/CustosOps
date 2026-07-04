from fastapi.testclient import TestClient

from app.main import app
from app.schemas.redaction_settings import RedactionSettingsResponse
from app.services import redaction_settings
from app.services.redaction_engine import redact_text, redact_value


client = TestClient(app)


def test_redaction_engine_applies_default_email_and_windows_profile_rules():
    settings = RedactionSettingsResponse(
        enabled=True,
        profile_name="test",
        updated_at="2026-01-01T00:00:00Z",
        rules=[
            {
                "rule_id": "email-addresses",
                "label": "Email addresses",
                "kind": "pattern",
                "value": "email",
                "enabled": True,
                "replacement": "[EMAIL]",
            },
            {
                "rule_id": "user-profile-paths",
                "label": "Windows user profile paths",
                "kind": "pattern",
                "value": "windows_user_profile_path",
                "enabled": True,
                "replacement": "C:\\Users\\[USER]",
            },
            {
                "rule_id": "ipv4-addresses",
                "label": "IPv4 addresses",
                "kind": "pattern",
                "value": "ipv4",
                "enabled": False,
                "replacement": "[IP]",
            },
        ],
    )

    redacted, applied = redact_text(
        "Contact analyst@example.com and inspect C:\\Users\\analyst\\Desktop\\file.txt from 192.168.1.10",
        settings=settings,
    )

    assert "analyst@example.com" not in redacted
    assert "C:\\Users\\analyst" not in redacted
    assert "192.168.1.10" in redacted
    assert "email-addresses" in applied
    assert "user-profile-paths" in applied
    assert "ipv4-addresses" not in applied


def test_redaction_engine_can_redact_nested_values():
    settings = RedactionSettingsResponse(
        enabled=True,
        profile_name="test",
        updated_at="2026-01-01T00:00:00Z",
        rules=[
            {
                "rule_id": "email-addresses",
                "label": "Email addresses",
                "kind": "pattern",
                "value": "email",
                "enabled": True,
                "replacement": "[EMAIL]",
            }
        ],
    )

    value = {
        "message": "User analyst@example.com failed test",
        "items": ["admin@example.com", 10],
    }

    redacted = redact_value(value, settings=settings)

    assert redacted["message"] == "User [EMAIL] failed test"
    assert redacted["items"][0] == "[EMAIL]"
    assert redacted["items"][1] == 10


def test_redaction_preview_api_uses_saved_settings(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"

    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_DIR", tmp_path)
    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_PATH", settings_path)

    reset_response = client.post("/api/redaction/settings/reset")
    assert reset_response.status_code == 200

    response = client.post(
        "/api/redaction/preview",
        json={
            "text": "Contact analyst@example.com from C:\\Users\\analyst\\Desktop"
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert data["changed"] is True
    assert "analyst@example.com" not in data["redacted"]
    assert "C:\\Users\\analyst" not in data["redacted"]
    assert "email-addresses" in data["applied_rules"]
    assert "user-profile-paths" in data["applied_rules"]
