import re

from app.schemas.app_log import AppLogEntry, AppLogEvidence


HTTP_PATTERN = re.compile(
    r'"?(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+([^\s"]+)(?:\s+HTTP/[0-9.]+)?"?\s+(\d{3})',
    re.IGNORECASE,
)

TIMESTAMP_PATTERN = re.compile(
    r"\b(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?Z?)\b"
)

LEVEL_PATTERN = re.compile(r"\b(CRITICAL|ERROR|ERR|WARNING|WARN|INFO|DEBUG)\b", re.IGNORECASE)

IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

LATENCY_PATTERN = re.compile(
    r"\b(?:latency|duration|elapsed|took|time)[=: ]+(\d+(?:\.\d+)?)\s*(ms|milliseconds|s|sec|seconds)\b",
    re.IGNORECASE,
)

SENSITIVE_PATTERNS = {
    "authorization_header": re.compile(r"authorization:\s*(bearer|basic)\s+\S+", re.IGNORECASE),
    "bearer_token": re.compile(r"\bbearer\s+[A-Za-z0-9._\-]{20,}", re.IGNORECASE),
    "password_value": re.compile(r"\bpassword\s*[=:]\s*\S+", re.IGNORECASE),
    "api_key_value": re.compile(r"\bapi[_-]?key\s*[=:]\s*\S+", re.IGNORECASE),
    "token_value": re.compile(r"\btoken\s*[=:]\s*\S+", re.IGNORECASE),
    "connection_string": re.compile(r"\b(server|database|uid|user id|pwd)\s*=", re.IGNORECASE),
}


def parse_app_log(filename: str, content: str) -> AppLogEvidence:
    lines = content.splitlines()
    entries: list[AppLogEntry] = []
    sensitive_indicators: set[str] = set()

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped == "":
            continue

        for name, pattern in SENSITIVE_PATTERNS.items():
            if pattern.search(stripped):
                sensitive_indicators.add(name)

        timestamp = _extract_timestamp(stripped)
        level = _extract_level(stripped)
        client_ip = _extract_client_ip(stripped)
        http_method, path, status_code = _extract_http(stripped)
        latency_ms = _extract_latency_ms(stripped)

        entries.append(
            AppLogEntry(
                line_number=index,
                raw=stripped[:1000],
                timestamp=timestamp,
                level=level,
                source=filename,
                client_ip=client_ip,
                http_method=http_method,
                path=path,
                status_code=status_code,
                latency_ms=latency_ms,
            )
        )

    warnings: list[str] = []

    if len(lines) == 0:
        warnings.append("The imported log file is empty.")

    if entries and all(entry.status_code is None for entry in entries):
        warnings.append("No HTTP status codes were detected. Generic text rules were still applied.")

    return AppLogEvidence(
        source_file=filename,
        raw_line_count=len(lines),
        parsed_entry_count=len(entries),
        entries=entries,
        sensitive_indicators=sorted(sensitive_indicators),
        parser_warnings=warnings,
    )


def _extract_timestamp(line: str) -> str | None:
    match = TIMESTAMP_PATTERN.search(line)
    return match.group(1) if match else None


def _extract_level(line: str) -> str | None:
    match = LEVEL_PATTERN.search(line)

    if match:
        value = match.group(1).upper()

        if value == "ERR":
            return "ERROR"

        if value == "WARN":
            return "WARNING"

        return value

    lowered = line.lower()

    if "traceback" in lowered or "exception" in lowered or "unhandled" in lowered:
        return "ERROR"

    return None


def _extract_client_ip(line: str) -> str | None:
    match = IP_PATTERN.search(line)
    return match.group(0) if match else None


def _extract_http(line: str) -> tuple[str | None, str | None, int | None]:
    match = HTTP_PATTERN.search(line)

    if not match:
        return None, None, None

    return match.group(1).upper(), match.group(2), int(match.group(3))


def _extract_latency_ms(line: str) -> float | None:
    match = LATENCY_PATTERN.search(line)

    if not match:
        return None

    value = float(match.group(1))
    unit = match.group(2).lower()

    if unit in {"s", "sec", "seconds"}:
        return value * 1000

    return value