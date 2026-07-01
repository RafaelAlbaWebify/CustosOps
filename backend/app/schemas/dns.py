from typing import Any

from pydantic import BaseModel, Field


class DnsRecordEvidence(BaseModel):
    host_name: str
    record_type: str = "A"
    ip_address: str | None = None
    alias_target: str | None = None
    zone: str | None = None
    dns_server: str | None = None
    forward_status: str | None = None
    ptr_status: str | None = None
    ping_status: str | None = None
    age_days: int | None = None
    is_duplicate_ip: bool | None = None
    notes: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class DnsEvidence(BaseModel):
    schema_version: str = "custosops.dns.v0.1"
    collected_at: str | None = None
    collector: str | None = None
    collector_mode: str = "read_only"
    source_file: str | None = None
    records: list[DnsRecordEvidence] = Field(default_factory=list)
    safety: dict[str, Any] = Field(default_factory=dict)


class DnsCsvImportRequest(BaseModel):
    filename: str = "dns-audit.csv"
    content: str


class DnsCsvImportResponse(BaseModel):
    evidence: DnsEvidence
    parsed_record_count: int
    ignored_row_count: int
    warnings: list[str] = Field(default_factory=list)