import csv
import io
import json
import re
from typing import Any

from app.schemas.windows_event import WindowsEventEvidence, WindowsEventRecord


def parse_windows_event_evidence(filename: str, content: str) -> WindowsEventEvidence:
    rows, warnings = _load_rows(content)
    events: list[WindowsEventRecord] = []

    for index, row in enumerate(rows, start=1):
        normalized = _normalize_row(row)

        events.append(
            WindowsEventRecord(
                record_number=_to_int(_first(normalized, "recordid", "recordnumber", "record_id")),
                timestamp=_first(normalized, "timecreated", "timestamp", "datetime", "date", "time"),
                provider=_first(normalized, "providername", "provider", "source", "source_name"),
                event_id=_to_int(_first(normalized, "id", "eventid", "event_id", "eventcode")),
                level=_normalize_level(_first(normalized, "leveldisplayname", "level", "entrytype", "type", "severity")),
                computer=_first(normalized, "machinename", "computer", "computername", "hostname", "host"),
                log_name=_first(normalized, "logname", "channel", "log"),
                user=_first(normalized, "user", "username", "accountname", "targetusername"),
                message=_first(normalized, "message", "rendereddescription", "description", "eventdata") or "",
                raw=row,
            )
        )

    if not events:
        warnings.append("No Windows Event records were parsed.")

    return WindowsEventEvidence(
        source_file=filename,
        raw_event_count=len(rows),
        parsed_event_count=len(events),
        events=events,
        parser_warnings=warnings,
    )


def _load_rows(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    stripped = content.strip()

    if not stripped:
        return [], ["The imported Windows Event evidence file is empty."]

    try:
        parsed = json.loads(stripped)

        if isinstance(parsed, list):
            return [_as_dict(item) for item in parsed], warnings

        if isinstance(parsed, dict):
            if isinstance(parsed.get("events"), list):
                return [_as_dict(item) for item in parsed["events"]], warnings

            if isinstance(parsed.get("records"), list):
                return [_as_dict(item) for item in parsed["records"]], warnings

            return [parsed], warnings
    except json.JSONDecodeError:
        pass

    try:
        reader = csv.DictReader(io.StringIO(content))
        rows = [dict(row) for row in reader if row]
        return rows, warnings
    except csv.Error as exc:
        warnings.append(f"CSV parser warning: {exc}")
        return [], warnings


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    return {_normalize_key(key): value for key, value in row.items()}


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())


def _first(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = row.get(_normalize_key(key))

        if value is not None and str(value).strip() != "":
            return str(value).strip()

    return None


def _to_int(value: Any) -> int | None:
    if value is None:
        return None

    match = re.search(r"\d+", str(value))

    if not match:
        return None

    return int(match.group(0))


def _normalize_level(value: str | None) -> str | None:
    if value is None:
        return None

    raw = str(value).strip()
    lowered = raw.lower()

    if lowered in {"1", "critical"}:
        return "Critical"

    if lowered in {"2", "error"}:
        return "Error"

    if lowered in {"3", "warning", "warn"}:
        return "Warning"

    if lowered in {"4", "information", "info"}:
        return "Information"

    return raw


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    return {}
