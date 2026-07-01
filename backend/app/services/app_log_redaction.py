import re
from typing import Any


REDACTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"authorization:\s*(bearer|basic)\s+[A-Za-z0-9._:/+=\-]+", re.IGNORECASE),
        "Authorization: [REDACTED_AUTH_HEADER]",
    ),
    (
        re.compile(r"\bbearer\s+[A-Za-z0-9._:/+=\-]{12,}", re.IGNORECASE),
        "Bearer [REDACTED_BEARER_TOKEN]",
    ),
    (
        re.compile(r"\bpassword\s*[=:]\s*[^\s&;,]+", re.IGNORECASE),
        "password=[REDACTED_PASSWORD]",
    ),
    (
        re.compile(r"\bpwd\s*=\s*[^\s&;,]+", re.IGNORECASE),
        "pwd=[REDACTED_PASSWORD]",
    ),
    (
        re.compile(r"\btoken\s*[=:]\s*[^\s&;,]+", re.IGNORECASE),
        "token=[REDACTED_TOKEN]",
    ),
    (
        re.compile(r"\bapi[_-]?key\s*[=:]\s*[^\s&;,]+", re.IGNORECASE),
        "api_key=[REDACTED_API_KEY]",
    ),
    (
        re.compile(r"\bsecret\s*[=:]\s*[^\s&;,]+", re.IGNORECASE),
        "secret=[REDACTED_SECRET]",
    ),
]


def redact_text(value: Any) -> str:
    text = str(value)

    for pattern, replacement in REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)

    return text


def redact_obj(value: Any) -> Any:
    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, list):
        return [redact_obj(item) for item in value]

    if isinstance(value, tuple):
        return [redact_obj(item) for item in value]

    if isinstance(value, dict):
        return {key: redact_obj(item) for key, item in value.items()}

    if hasattr(value, "model_dump"):
        return redact_obj(value.model_dump())

    return value
