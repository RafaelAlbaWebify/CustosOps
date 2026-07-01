from collections import Counter
from typing import Any


def build_api_error_summary(evidence: Any) -> dict[str, Any]:
    evidence_dict = _as_dict(evidence)
    entries = [_as_dict(entry) for entry in evidence_dict.get("entries", [])]

    http_entries = [entry for entry in entries if entry.get("status_code") is not None]
    failing_entries = [entry for entry in http_entries if int(entry.get("status_code") or 0) >= 400]
    server_error_entries = [entry for entry in http_entries if int(entry.get("status_code") or 0) >= 500]
    auth_failure_entries = [entry for entry in http_entries if int(entry.get("status_code") or 0) in {401, 403}]
    not_found_entries = [entry for entry in http_entries if int(entry.get("status_code") or 0) == 404]
    slow_entries = [
        entry
        for entry in entries
        if entry.get("latency_ms") is not None and float(entry.get("latency_ms") or 0) >= 1000
    ]

    status_counts = Counter(str(entry.get("status_code")) for entry in http_entries if entry.get("status_code") is not None)
    failing_endpoint_counts = Counter(
        str(entry.get("path") or "unknown")
        for entry in failing_entries
    )
    client_ip_counts = Counter(
        str(entry.get("client_ip"))
        for entry in failing_entries
        if entry.get("client_ip")
    )

    timestamps = sorted(
        str(entry.get("timestamp"))
        for entry in entries
        if entry.get("timestamp")
    )

    slowest_requests = sorted(
        slow_entries,
        key=lambda entry: float(entry.get("latency_ms") or 0),
        reverse=True,
    )[:5]

    return {
        "http_request_count": len(http_entries),
        "failure_count": len(failing_entries),
        "server_error_count": len(server_error_entries),
        "auth_failure_count": len(auth_failure_entries),
        "not_found_count": len(not_found_entries),
        "slow_request_count": len(slow_entries),
        "status_code_breakdown": dict(status_counts),
        "top_failing_endpoints": [
            {"endpoint": endpoint, "count": count}
            for endpoint, count in failing_endpoint_counts.most_common(5)
        ],
        "top_client_ips": [
            {"client_ip": client_ip, "count": count}
            for client_ip, count in client_ip_counts.most_common(5)
        ],
        "slowest_requests": [
            {
                "path": entry.get("path") or "unknown",
                "status_code": entry.get("status_code"),
                "latency_ms": entry.get("latency_ms"),
                "client_ip": entry.get("client_ip"),
                "line_number": entry.get("line_number"),
            }
            for entry in slowest_requests
        ],
        "first_seen": timestamps[0] if timestamps else None,
        "last_seen": timestamps[-1] if timestamps else None,
    }


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump()

    if hasattr(value, "dict"):
        return value.dict()

    return {}
