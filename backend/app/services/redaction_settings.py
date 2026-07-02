import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.redaction_settings import RedactionSettingsResponse, RedactionSettingsUpdateRequest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REDACTION_SETTINGS_DIR = PROJECT_ROOT / "reports" / "custosops_redaction"
REDACTION_SETTINGS_PATH = REDACTION_SETTINGS_DIR / "settings.json"


DEFAULT_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "email-addresses",
        "label": "Email addresses",
        "kind": "pattern",
        "value": "email",
        "enabled": True,
        "replacement": "[REDACTED_EMAIL]",
        "description": "Redact email addresses from evidence previews and reports.",
    },
    {
        "rule_id": "user-profile-paths",
        "label": "Windows user profile paths",
        "kind": "pattern",
        "value": "windows_user_profile_path",
        "enabled": True,
        "replacement": "C:\\Users\\[REDACTED_USER]",
        "description": "Redact local Windows profile names from paths.",
    },
    {
        "rule_id": "ipv4-addresses",
        "label": "IPv4 addresses",
        "kind": "pattern",
        "value": "ipv4",
        "enabled": False,
        "replacement": "[REDACTED_IP]",
        "description": "Optional. Redacting IP addresses can reduce operational usefulness.",
    },
    {
        "rule_id": "hostnames",
        "label": "Hostnames",
        "kind": "field",
        "value": "hostname",
        "enabled": False,
        "replacement": "[REDACTED_HOST]",
        "description": "Optional. Hostnames are often needed for operational evidence review.",
    },
]


def get_redaction_settings() -> RedactionSettingsResponse:
    raw = _read_settings_file()

    if raw is None:
        return default_redaction_settings()

    try:
        return RedactionSettingsResponse.model_validate(raw)
    except Exception:
        return default_redaction_settings()


def save_redaction_settings(request: RedactionSettingsUpdateRequest) -> RedactionSettingsResponse:
    REDACTION_SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

    response = RedactionSettingsResponse(
        **request.model_dump(),
        updated_at=_utc_now(),
    )

    REDACTION_SETTINGS_PATH.write_text(
        json.dumps(response.model_dump(), indent=2),
        encoding="utf-8",
    )

    return response


def reset_redaction_settings() -> RedactionSettingsResponse:
    return save_redaction_settings(
        RedactionSettingsUpdateRequest(
            enabled=True,
            profile_name="default-local",
            rules=DEFAULT_RULES,
        )
    )


def default_redaction_settings() -> RedactionSettingsResponse:
    return RedactionSettingsResponse(
        enabled=True,
        profile_name="default-local",
        rules=DEFAULT_RULES,
        updated_at=_utc_now(),
    )


def _read_settings_file() -> dict[str, Any] | None:
    if not REDACTION_SETTINGS_PATH.exists():
        return None

    try:
        parsed = json.loads(REDACTION_SETTINGS_PATH.read_text(encoding="utf-8-sig"))

        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None

    return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
