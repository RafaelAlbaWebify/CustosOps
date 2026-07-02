import re
from typing import Iterable

from app.schemas.redaction_settings import RedactionRule, RedactionSettingsResponse
from app.services.redaction_settings import get_redaction_settings


EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
IPV4_PATTERN = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
WINDOWS_PROFILE_PATTERN = re.compile(r"C:\\Users\\([^\\\r\n]+)", re.IGNORECASE)


def redact_text(text: str, settings: RedactionSettingsResponse | None = None) -> tuple[str, list[str]]:
    active_settings = settings or get_redaction_settings()

    if not active_settings.enabled:
        return text, []

    redacted = text
    applied_rules: list[str] = []

    for rule in active_settings.rules:
        if not rule.enabled:
            continue

        updated = _apply_rule(redacted, rule)

        if updated != redacted:
            redacted = updated
            applied_rules.append(rule.rule_id)

    return redacted, applied_rules


def redact_value(value: object, settings: RedactionSettingsResponse | None = None) -> object:
    if isinstance(value, str):
        redacted, _ = redact_text(value, settings=settings)
        return redacted

    if isinstance(value, list):
        return [redact_value(item, settings=settings) for item in value]

    if isinstance(value, dict):
        return {key: redact_value(item, settings=settings) for key, item in value.items()}

    return value


def _apply_rule(text: str, rule: RedactionRule) -> str:
    if rule.kind == "literal":
        if not rule.value:
            return text
        return text.replace(rule.value, rule.replacement)

    if rule.kind == "pattern":
        return _apply_pattern_rule(text, rule)

    if rule.kind == "field":
        return _apply_field_rule(text, rule)

    return text


def _apply_pattern_rule(text: str, rule: RedactionRule) -> str:
    if rule.value == "email":
        return EMAIL_PATTERN.sub(lambda match: rule.replacement, text)

    if rule.value == "ipv4":
        return IPV4_PATTERN.sub(lambda match: rule.replacement, text)

    if rule.value == "windows_user_profile_path":
        return WINDOWS_PROFILE_PATTERN.sub(lambda match: rule.replacement, text)

    try:
        return re.sub(rule.value, lambda match: rule.replacement, text)
    except re.error:
        return text


def _apply_field_rule(text: str, rule: RedactionRule) -> str:
    # Field rules are mostly useful when redacting structured objects.
    # For plain text previews, only apply a conservative literal match.
    if not rule.value:
        return text

    return text.replace(rule.value, rule.replacement)


def collect_applied_rule_ids(results: Iterable[tuple[str, list[str]]]) -> list[str]:
    ordered: list[str] = []

    for _, rule_ids in results:
        for rule_id in rule_ids:
            if rule_id not in ordered:
                ordered.append(rule_id)

    return ordered
