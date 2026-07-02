from fastapi.testclient import TestClient

from app.main import app
from app.services import redaction_settings


client = TestClient(app)


def test_redaction_settings_default_update_and_reset(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"

    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_DIR", tmp_path)
    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_PATH", settings_path)

    default_response = client.get("/api/redaction/settings")
    assert default_response.status_code == 200

    default_data = default_response.json()
    assert default_data["enabled"] is True
    assert default_data["profile_name"] == "default-local"
    assert len(default_data["rules"]) >= 2

    update_response = client.put(
        "/api/redaction/settings",
        json={
            "enabled": True,
            "profile_name": "operator-review",
            "rules": [
                {
                    "rule_id": "emails-only",
                    "label": "Emails only",
                    "kind": "pattern",
                    "value": "email",
                    "enabled": True,
                    "replacement": "[EMAIL]",
                    "description": "Test profile",
                }
            ],
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["profile_name"] == "operator-review"
    assert updated["rules"][0]["rule_id"] == "emails-only"
    assert updated["updated_at"].endswith("Z")

    persisted_response = client.get("/api/redaction/settings")
    assert persisted_response.status_code == 200
    assert persisted_response.json()["profile_name"] == "operator-review"

    reset_response = client.post("/api/redaction/settings/reset")
    assert reset_response.status_code == 200
    reset = reset_response.json()
    assert reset["profile_name"] == "default-local"
    assert any(rule["rule_id"] == "email-addresses" for rule in reset["rules"])


def test_redaction_settings_rejects_invalid_rule_kind(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"

    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_DIR", tmp_path)
    monkeypatch.setattr(redaction_settings, "REDACTION_SETTINGS_PATH", settings_path)

    response = client.put(
        "/api/redaction/settings",
        json={
            "enabled": True,
            "profile_name": "bad-profile",
            "rules": [
                {
                    "rule_id": "bad",
                    "label": "Bad",
                    "kind": "unsupported",
                    "value": "x",
                }
            ],
        },
    )

    assert response.status_code == 422
