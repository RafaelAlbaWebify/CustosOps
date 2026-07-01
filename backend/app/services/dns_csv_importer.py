import csv
import io
import re
from datetime import datetime, timezone
from typing import Any

from app.schemas.dns import DnsCsvImportResponse, DnsEvidence, DnsRecordEvidence


def import_dns_audit_csv(filename: str, content: str) -> DnsCsvImportResponse:
    clean_content = content.lstrip("\ufeff")
    warnings: list[str] = []

    if not clean_content.strip():
        return DnsCsvImportResponse(
            evidence=_empty_evidence(filename),
            parsed_record_count=0,
            ignored_row_count=0,
            warnings=["CSV content was empty."],
        )

    dialect = _detect_dialect(clean_content)
    reader = csv.DictReader(io.StringIO(clean_content), dialect=dialect)

    if not reader.fieldnames:
        return DnsCsvImportResponse(
            evidence=_empty_evidence(filename),
            parsed_record_count=0,
            ignored_row_count=0,
            warnings=["CSV header row was not detected."],
        )

    records: list[DnsRecordEvidence] = []
    ignored_rows = 0

    for row in reader:
        if not row or all(str(value or "").strip() == "" for value in row.values()):
            ignored_rows += 1
            continue

        normalized = {_normalize_header(key): value for key, value in row.items() if key is not None}

        record = _row_to_record(normalized, row)
        if record is None:
            ignored_rows += 1
            continue

        records.append(record)

    if not records:
        warnings.append("No DNS records could be parsed from the CSV.")

    evidence = DnsEvidence(
        schema_version="custosops.dns.v0.1",
        collected_at=datetime.now(timezone.utc).isoformat(),
        collector="dns_csv_import",
        collector_mode="read_only",
        source_file=filename,
        records=records,
        safety={
            "changed_configuration": False,
            "collected_credentials": False,
            "remediation_performed": False,
        },
    )

    return DnsCsvImportResponse(
        evidence=evidence,
        parsed_record_count=len(records),
        ignored_row_count=ignored_rows,
        warnings=warnings,
    )


def _empty_evidence(filename: str) -> DnsEvidence:
    return DnsEvidence(
        schema_version="custosops.dns.v0.1",
        collected_at=datetime.now(timezone.utc).isoformat(),
        collector="dns_csv_import",
        collector_mode="read_only",
        source_file=filename,
        records=[],
        safety={
            "changed_configuration": False,
            "collected_credentials": False,
            "remediation_performed": False,
        },
    )


def _detect_dialect(content: str) -> csv.Dialect:
    sample = content[:4096]

    try:
        return csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        return csv.excel


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower().lstrip("\ufeff"))


def _first(row: dict[str, Any], names: list[str]) -> str | None:
    for name in names:
        value = row.get(name)
        if value is not None and str(value).strip() != "":
            return str(value).strip()

    return None


def _row_to_record(normalized: dict[str, Any], raw: dict[str, Any]) -> DnsRecordEvidence | None:
    host = _first(
        normalized,
        [
            "hostname",
            "host",
            "name",
            "recordname",
            "record",
            "fqdn",
            "dnsname",
            "computername",
        ],
    )

    zone = _first(
        normalized,
        [
            "zone",
            "zonename",
            "dnszone",
            "forwardzone",
            "domain",
        ],
    )

    if host and not zone and "." in host:
        parts = host.split(".")
        if len(parts) > 2:
            zone = ".".join(parts[1:])

    if not host:
        return None

    record_type = _first(
        normalized,
        [
            "recordtype",
            "type",
            "dnstype",
        ],
    ) or "A"

    record_type = record_type.upper()

    record_data = _first(
        normalized,
        [
            "recorddata",
            "data",
            "target",
            "value",
        ],
    )

    ip_address = _first(
        normalized,
        [
            "ipaddress",
            "ip",
            "address",
            "ipv4",
            "targetip",
            "recordip",
        ],
    )

    alias_target = _first(
        normalized,
        [
            "aliastarget",
            "cnametarget",
            "targethost",
        ],
    )

    if record_type == "A" and not ip_address and record_data:
        ip_address = record_data

    if record_type == "CNAME" and not alias_target and record_data:
        alias_target = record_data

    dns_server = _first(
        normalized,
        [
            "dnsserver",
            "server",
            "nameserver",
            "dc",
        ],
    )

    forward_status = _first(
        normalized,
        [
            "forwardstatus",
            "forward",
            "forwardresolution",
            "resolutionstatus",
            "aresolutionstatus",
        ],
    )

    ptr_status = _first(
        normalized,
        [
            "ptrstatus",
            "ptr",
            "reversestatus",
            "reversednsstatus",
            "rdnsstatus",
        ],
    )

    ping_status = _first(
        normalized,
        [
            "pingstatus",
            "ping",
            "reachable",
            "icmpstatus",
        ],
    )

    notes = _first(
        normalized,
        [
            "notes",
            "note",
            "comment",
            "comments",
            "finding",
            "statusdetail",
        ],
    )

    age_raw = _first(
        normalized,
        [
            "agedays",
            "age",
            "staledays",
            "daysold",
            "recordagedays",
        ],
    )

    duplicate_raw = _first(
        normalized,
        [
            "isduplicateip",
            "duplicateip",
            "dupip",
            "sharedip",
            "duplicatedip",
        ],
    )

    return DnsRecordEvidence(
        host_name=host,
        record_type=record_type,
        ip_address=ip_address,
        alias_target=alias_target,
        zone=zone,
        dns_server=dns_server,
        forward_status=forward_status,
        ptr_status=ptr_status,
        ping_status=ping_status,
        age_days=_parse_int(age_raw),
        is_duplicate_ip=_parse_bool(duplicate_raw),
        notes=notes,
        raw={str(key): value for key, value in raw.items()},
    )


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None

    stripped = value.strip()
    if stripped == "":
        return None

    try:
        return int(float(stripped))
    except ValueError:
        return None


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None

    lowered = value.strip().lower()

    if lowered in {"true", "yes", "y", "1", "duplicate", "duplicated", "shared"}:
        return True

    if lowered in {"false", "no", "n", "0", "unique"}:
        return False

    return None