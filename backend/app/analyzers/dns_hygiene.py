from collections import Counter

from app.schemas.dns import DnsEvidence, DnsRecordEvidence
from app.schemas.finding import EvidenceItem, SecurityFinding


def _asset(record: DnsRecordEvidence) -> str:
    zone = record.zone or "unknown-zone"
    host = record.host_name or "unknown-host"
    return f"{host}.{zone}" if zone not in host else host


def _evidence(source: str, key: str, value: object) -> EvidenceItem:
    return EvidenceItem(source=source, key=key, value=str(value))


def analyze_dns_evidence(evidence: DnsEvidence) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []

    records = evidence.records
    ip_counts = Counter(
        record.ip_address
        for record in records
        if record.ip_address and record.record_type.upper() == "A"
    )

    for record in records:
        host_asset = _asset(record)
        record_type = record.record_type.upper()

        if record.forward_status and record.forward_status.upper() not in {"OK", "FORWARD_OK"}:
            findings.append(
                SecurityFinding(
                    finding_id="DNS_FORWARD_NOT_OK",
                    title="DNS forward resolution is not confirmed healthy",
                    severity="medium",
                    confidence="medium",
                    category="DNS hygiene",
                    affected_asset=host_asset,
                    evidence=[
                        _evidence("dns", "forward_status", record.forward_status),
                        _evidence("dns", "record_type", record_type),
                        _evidence("dns", "ip_address", record.ip_address or "n/a"),
                    ],
                    why_it_matters=(
                        "Forward DNS inconsistency can cause application, authentication, "
                        "endpoint management, and support symptoms that appear unrelated to DNS."
                    ),
                    limitations=[
                        "This finding depends on the quality and freshness of the imported DNS evidence.",
                        "Business ownership and expected record state must be validated before cleanup.",
                    ],
                    safe_next_steps=[
                        "Validate the hostname from the expected DNS server.",
                        "Confirm whether the record is still owned by an active asset or service.",
                        "Prepare cleanup through normal DNS change control if the record is stale or incorrect.",
                    ],
                    non_actions=[
                        "Do not delete DNS records without confirming ownership and business impact.",
                    ],
                )
            )

        if record.ptr_status and record.ptr_status.upper() in {"NO_PTR", "PTR_MISMATCH", "PTR_MULTIPLE", "MISMATCH"}:
            findings.append(
                SecurityFinding(
                    finding_id="DNS_PTR_NOT_HEALTHY",
                    title="Reverse DNS is missing or inconsistent",
                    severity="low" if record.ptr_status.upper() == "NO_PTR" else "medium",
                    confidence="medium",
                    category="DNS hygiene",
                    affected_asset=host_asset,
                    evidence=[
                        _evidence("dns", "ptr_status", record.ptr_status),
                        _evidence("dns", "ip_address", record.ip_address or "n/a"),
                    ],
                    why_it_matters=(
                        "Reverse DNS inconsistencies can reduce troubleshooting quality, "
                        "make asset ownership unclear, and complicate infrastructure hygiene reviews."
                    ),
                    limitations=[
                        "Missing PTR records may be acceptable for some environments.",
                        "Reverse-zone ownership may be separate from forward-zone ownership.",
                    ],
                    safe_next_steps=[
                        "Confirm whether PTR records are expected for this subnet.",
                        "Validate the correct hostname-to-IP relationship.",
                        "Document or correct the reverse record through change control.",
                    ],
                    non_actions=[
                        "Do not create or modify PTR records without confirming reverse-zone ownership.",
                    ],
                )
            )

        if record.age_days is not None and record.age_days >= 90:
            findings.append(
                SecurityFinding(
                    finding_id="DNS_POTENTIAL_STALE_RECORD",
                    title="DNS record appears potentially stale",
                    severity="medium",
                    confidence="low",
                    category="Infrastructure hygiene",
                    affected_asset=host_asset,
                    evidence=[
                        _evidence("dns", "age_days", record.age_days),
                        _evidence("dns", "ping_status", record.ping_status or "unknown"),
                    ],
                    why_it_matters=(
                        "Old or unreachable DNS records can hide decommissioning gaps, "
                        "confuse troubleshooting, and increase operational risk."
                    ),
                    limitations=[
                        "Record age alone does not prove the asset is decommissioned.",
                        "Some stable infrastructure records may be old and still valid.",
                    ],
                    safe_next_steps=[
                        "Confirm asset ownership.",
                        "Check whether the asset still exists in endpoint, server, DHCP, or CMDB records.",
                        "Mark for cleanup review if no owner or active asset is found.",
                    ],
                    non_actions=[
                        "Do not delete stale-looking records based only on age.",
                    ],
                )
            )

        if record.ip_address and ip_counts[record.ip_address] > 1:
            findings.append(
                SecurityFinding(
                    finding_id="DNS_SHARED_IP_REVIEW_REQUIRED",
                    title="Multiple DNS names share the same IP address",
                    severity="low",
                    confidence="medium",
                    category="DNS hygiene",
                    affected_asset=host_asset,
                    evidence=[
                        _evidence("dns", "ip_address", record.ip_address),
                        _evidence("dns", "name_count_for_ip", ip_counts[record.ip_address]),
                    ],
                    why_it_matters=(
                        "Shared IP records may be valid aliases, but they can also indicate "
                        "legacy naming, migration leftovers, or unclear service ownership."
                    ),
                    limitations=[
                        "Shared IP usage is often legitimate for aliases, load balancers, or hosted services.",
                    ],
                    safe_next_steps=[
                        "Review whether the shared IP relationship is intentional.",
                        "Document service ownership and alias purpose.",
                    ],
                    non_actions=[
                        "Do not remove aliases without confirming application dependencies.",
                    ],
                )
            )

    if not findings:
        findings.append(
            SecurityFinding(
                finding_id="DNS_HYGIENE_NO_MAJOR_FINDINGS",
                title="No major DNS hygiene findings in current evidence",
                severity="info",
                confidence="medium",
                category="DNS hygiene",
                affected_asset="dns-evidence",
                evidence=[_evidence("dns", "analysis_result", "no_major_findings")],
                why_it_matters="The current DNS evidence did not trigger the initial CustosOps DNS hygiene rules.",
                limitations=[
                    "This is not a full DNS security assessment.",
                    "Public DNS exposure, SPF/DKIM/DMARC, and TLS checks are not included yet.",
                ],
                safe_next_steps=[
                    "Continue with identity, Microsoft 365, and external exposure modules.",
                ],
                non_actions=[
                    "Do not treat this as proof of complete DNS security compliance.",
                ],
            )
        )

    return findings