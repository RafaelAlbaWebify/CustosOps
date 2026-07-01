from collections import Counter

from app.schemas.app_log import AppLogEntry, AppLogEvidence
from app.services.app_log_redaction import redact_text


def analyze_app_log_evidence(evidence: AppLogEvidence) -> list[dict]:
    findings: list[dict] = []
    entries = evidence.entries

    _add_http_5xx_findings(findings, evidence, entries)
    _add_auth_failure_findings(findings, evidence, entries)
    _add_404_findings(findings, evidence, entries)
    _add_timeout_findings(findings, evidence, entries)
    _add_dns_findings(findings, evidence, entries)
    _add_tls_findings(findings, evidence, entries)
    _add_database_findings(findings, evidence, entries)
    _add_exception_findings(findings, evidence, entries)
    _add_slow_request_findings(findings, evidence, entries)
    _add_sensitive_data_findings(findings, evidence)

    return findings


def _add_http_5xx_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [entry for entry in entries if entry.status_code is not None and entry.status_code >= 500]

    if not matches:
        return

    affected = _most_common_path(matches) or evidence.source_file
    codes = Counter(str(entry.status_code) for entry in matches if entry.status_code is not None)

    findings.append(
        _finding(
            finding_id="APP_LOG_HTTP_5XX_ERRORS",
            title="Application log contains HTTP server errors",
            severity="high",
            confidence="medium",
            category="Application runtime evidence",
            affected_asset=affected,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("error_count", str(len(matches))),
                ("status_codes", _counter_summary(codes)),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "HTTP 5xx responses usually indicate backend, dependency, configuration, or runtime failures. "
                "They are operationally important because users may experience failed transactions even when the host is reachable."
            ),
            safe_next_steps=[
                "Identify the first observed 5xx timestamp and affected endpoint.",
                "Check related application, dependency, database, and deployment events in the same time window.",
                "Confirm whether errors are isolated, recurring, or increasing.",
            ],
            limitations=[
                "A log sample may not represent the full incident window.",
                "The HTTP status alone does not prove root cause.",
            ],
            non_actions=[
                "Do not restart services blindly without checking active transactions and dependency health.",
                "Do not treat this as proof of exploitation.",
            ],
        )
    )


def _add_auth_failure_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [entry for entry in entries if entry.status_code in {401, 403}]

    if not matches:
        return

    affected = _most_common_path(matches) or evidence.source_file
    codes = Counter(str(entry.status_code) for entry in matches if entry.status_code is not None)

    findings.append(
        _finding(
            finding_id="APP_LOG_AUTH_FAILURES",
            title="Application log contains authentication or authorization failures",
            severity="medium",
            confidence="medium",
            category="Application access evidence",
            affected_asset=affected,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("auth_failure_count", str(len(matches))),
                ("status_codes", _counter_summary(codes)),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "Repeated 401 or 403 responses can indicate expired credentials, wrong permissions, broken SSO integration, "
                "API token issues, or clients using an incorrect authentication flow."
            ),
            safe_next_steps=[
                "Confirm whether the affected client or user was expected to access the endpoint.",
                "Check token expiry, role assignment, SSO claims, and recent permission changes.",
                "Compare failed requests with successful requests for the same endpoint.",
            ],
            limitations=[
                "401 and 403 responses can be normal for unauthenticated probes or expired sessions.",
                "User identity may not be visible in the imported log sample.",
            ],
            non_actions=[
                "Do not grant broader permissions without confirming the expected access model.",
                "Do not expose tokens or authorization headers in reports.",
            ],
        )
    )


def _add_404_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [entry for entry in entries if entry.status_code == 404]

    if len(matches) < 2:
        return

    affected = _most_common_path(matches) or evidence.source_file

    findings.append(
        _finding(
            finding_id="APP_LOG_REPEATED_404_RESPONSES",
            title="Application log contains repeated 404 responses",
            severity="low",
            confidence="medium",
            category="Application routing evidence",
            affected_asset=affected,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("not_found_count", str(len(matches))),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "Repeated 404 responses can indicate outdated client URLs, missing routes, deployment mismatch, broken links, "
                "or integration clients calling the wrong endpoint."
            ),
            safe_next_steps=[
                "Validate whether the requested path still exists.",
                "Check recent route, reverse proxy, or deployment changes.",
                "Confirm whether the caller is using the current API version.",
            ],
            limitations=[
                "Some 404s are normal noise, especially for scanners or browsers requesting missing assets.",
            ],
            non_actions=[
                "Do not classify 404s as a backend outage without checking expected routes.",
            ],
        )
    )


def _add_timeout_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [entry for entry in entries if _contains_any(entry.raw, ["timeout", "timed out", "deadline exceeded", "504 gateway timeout"])]

    if not matches:
        return

    findings.append(
        _finding(
            finding_id="APP_LOG_TIMEOUT_ERRORS",
            title="Application log contains timeout evidence",
            severity="high",
            confidence="medium",
            category="Application dependency evidence",
            affected_asset=evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("timeout_count", str(len(matches))),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "Timeouts often point to slow dependencies, database pressure, network path issues, thread exhaustion, "
                "or upstream services not responding in time."
            ),
            safe_next_steps=[
                "Identify the dependency or endpoint mentioned in the timeout.",
                "Check dependency health, latency, connection pool, and retry behavior.",
                "Compare timeout timestamps with infrastructure or deployment events.",
            ],
            limitations=[
                "The imported log may show the symptom but not the dependency that caused it.",
            ],
            non_actions=[
                "Do not increase timeout values before identifying the slow dependency.",
            ],
        )
    )


def _add_dns_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [
        entry
        for entry in entries
        if _contains_any(
            entry.raw,
            ["getaddrinfo", "name or service not known", "could not resolve", "dns lookup", "name resolution", "nodename nor servname"],
        )
    ]

    if not matches:
        return

    findings.append(
        _finding(
            finding_id="APP_LOG_DNS_RESOLUTION_ERRORS",
            title="Application log contains DNS or name-resolution errors",
            severity="medium",
            confidence="medium",
            category="Application dependency evidence",
            affected_asset=evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("dns_error_count", str(len(matches))),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "Name-resolution failures can make application errors appear like API or service failures even when the root cause is DNS, "
                "search suffix, resolver, or dependency naming."
            ),
            safe_next_steps=[
                "Identify the hostname that failed resolution.",
                "Validate DNS resolution from the same server or runtime context.",
                "Compare with DNS hygiene evidence if available.",
            ],
            limitations=[
                "The log may not include the DNS server used by the application host.",
            ],
            non_actions=[
                "Do not modify DNS records without confirming ownership and expected resolution.",
            ],
        )
    )


def _add_tls_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [
        entry
        for entry in entries
        if _contains_any(entry.raw, ["certificate verify failed", "ssl", "tls handshake", "certificate expired", "x509"])
    ]

    if not matches:
        return

    findings.append(
        _finding(
            finding_id="APP_LOG_TLS_CERTIFICATE_ERRORS",
            title="Application log contains TLS or certificate errors",
            severity="medium",
            confidence="medium",
            category="Application dependency evidence",
            affected_asset=evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("tls_error_count", str(len(matches))),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "TLS and certificate errors can break API integrations, service-to-service calls, webhooks, and authentication flows."
            ),
            safe_next_steps=[
                "Identify the remote endpoint involved.",
                "Check certificate expiry, trust chain, hostname match, and proxy interception.",
                "Validate the same call from the application host.",
            ],
            limitations=[
                "Some logs only show the TLS symptom and not the full certificate chain.",
            ],
            non_actions=[
                "Do not disable certificate validation as a workaround.",
            ],
        )
    )


def _add_database_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [
        entry
        for entry in entries
        if _contains_any(
            entry.raw,
            ["sql", "database", "db connection", "connection pool", "deadlock", "timeout expired", "could not connect to database"],
        )
    ]

    if not matches:
        return

    findings.append(
        _finding(
            finding_id="APP_LOG_DATABASE_DEPENDENCY_ERRORS",
            title="Application log contains database dependency errors",
            severity="high",
            confidence="medium",
            category="Application dependency evidence",
            affected_asset=evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("database_error_count", str(len(matches))),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "Database dependency errors can cause application failures even when the application service itself is running."
            ),
            safe_next_steps=[
                "Identify the query, connection, or database dependency mentioned.",
                "Check database availability, blocking, deadlocks, connection pool, and recent schema or deployment changes.",
                "Compare application error timing with database monitoring if available.",
            ],
            limitations=[
                "The log may not include database server-side evidence.",
            ],
            non_actions=[
                "Do not assume the application code is the only cause before checking the database dependency.",
            ],
        )
    )


def _add_exception_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [
        entry
        for entry in entries
        if entry.level in {"ERROR", "CRITICAL"} or _contains_any(entry.raw, ["traceback", "exception", "unhandled"])
    ]

    if not matches:
        return

    findings.append(
        _finding(
            finding_id="APP_LOG_UNHANDLED_EXCEPTIONS",
            title="Application log contains errors or exceptions",
            severity="high",
            confidence="medium",
            category="Application runtime evidence",
            affected_asset=evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("exception_or_error_count", str(len(matches))),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "Unhandled exceptions and error-level log entries are direct runtime evidence that the application experienced failure conditions."
            ),
            safe_next_steps=[
                "Group repeated exceptions by message and stack trace.",
                "Identify the first occurrence and any related deployment or configuration change.",
                "Check whether the same error affects one endpoint, one user, or all users.",
            ],
            limitations=[
                "Some applications log recoverable errors at ERROR level.",
            ],
            non_actions=[
                "Do not paste full stack traces with secrets into external systems.",
            ],
        )
    )


def _add_slow_request_findings(findings: list[dict], evidence: AppLogEvidence, entries: list[AppLogEntry]) -> None:
    matches = [entry for entry in entries if entry.latency_ms is not None and entry.latency_ms >= 2000]

    if not matches:
        return

    affected = _most_common_path(matches) or evidence.source_file
    max_latency = max(entry.latency_ms or 0 for entry in matches)

    findings.append(
        _finding(
            finding_id="APP_LOG_SLOW_REQUESTS",
            title="Application log contains slow request evidence",
            severity="medium",
            confidence="medium",
            category="Application performance evidence",
            affected_asset=affected,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("slow_request_count", str(len(matches))),
                ("max_latency_ms", str(round(max_latency, 2))),
                ("example_lines", _example_lines(matches)),
            ],
            why_it_matters=(
                "Slow requests may indicate dependency pressure, inefficient queries, resource saturation, or timeout risk."
            ),
            safe_next_steps=[
                "Identify whether slow requests affect one endpoint or multiple endpoints.",
                "Compare latency with dependency timing and infrastructure metrics.",
                "Check whether slow requests correlate with 5xx or timeout errors.",
            ],
            limitations=[
                "Latency parsing depends on whether the application logs timing values.",
            ],
            non_actions=[
                "Do not optimize blindly before identifying the slow component.",
            ],
        )
    )


def _add_sensitive_data_findings(findings: list[dict], evidence: AppLogEvidence) -> None:
    if not evidence.sensitive_indicators:
        return

    findings.append(
        _finding(
            finding_id="APP_LOG_SENSITIVE_DATA_INDICATORS",
            title="Application log may contain sensitive data indicators",
            severity="high",
            confidence="medium",
            category="Evidence handling",
            affected_asset=evidence.source_file,
            evidence_items=[
                ("source_file", evidence.source_file),
                ("sensitive_indicators", ", ".join(evidence.sensitive_indicators)),
            ],
            why_it_matters=(
                "Logs can accidentally expose authorization headers, tokens, passwords, connection strings, or other sensitive values. "
                "This affects evidence handling, report sharing, and incident review."
            ),
            safe_next_steps=[
                "Review whether sensitive values are present before sharing the log or report.",
                "Redact secrets from exported evidence.",
                "Check application logging configuration to avoid writing secrets.",
            ],
            limitations=[
                "Pattern detection can produce false positives.",
                "This does not prove a secret is valid or currently active.",
            ],
            non_actions=[
                "Do not upload unredacted logs to external tools.",
                "Do not include raw secrets in reports or tickets.",
            ],
        )
    )


def _finding(
    finding_id: str,
    title: str,
    severity: str,
    confidence: str,
    category: str,
    affected_asset: str,
    evidence_items: list[tuple[str, str]],
    why_it_matters: str,
    safe_next_steps: list[str],
    limitations: list[str],
    non_actions: list[str],
) -> dict:
    return {
        "finding_id": finding_id,
        "title": title,
        "severity": severity,
        "confidence": confidence,
        "category": category,
        "affected_asset": affected_asset,
        "evidence": [
            {
                "source": "application_log",
                "key": key,
                "value": value,
            }
            for key, value in evidence_items
        ],
        "why_it_matters": why_it_matters,
        "limitations": limitations,
        "safe_next_steps": safe_next_steps,
        "non_actions": non_actions,
    }


def _contains_any(value: str, needles: list[str]) -> bool:
    lowered = value.lower()
    return any(needle.lower() in lowered for needle in needles)


def _most_common_path(entries: list[AppLogEntry]) -> str | None:
    paths = [entry.path for entry in entries if entry.path]

    if not paths:
        return None

    return Counter(paths).most_common(1)[0][0]


def _counter_summary(counter: Counter) -> str:
    return ", ".join(f"{key}: {value}" for key, value in counter.most_common())


def _example_lines(entries: list[AppLogEntry], limit: int = 3) -> str:
    examples = []

    for entry in entries[:limit]:
        examples.append(f"line {entry.line_number}: {redact_text(entry.raw[:160])}")

    return " | ".join(examples)