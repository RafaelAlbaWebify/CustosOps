import json
from typing import Any

from pydantic import BaseModel, Field


class IisImportRequest(BaseModel):
    filename: str
    content: str


class IisPathCheck(BaseModel):
    path: str
    exists: bool


class IisServiceStatus(BaseModel):
    name: str
    display_name: str | None = None
    status: str | None = None
    start_type: str | None = None


class IisSite(BaseModel):
    name: str | None = None
    site_id: str | None = None
    state: str | None = None
    bindings: list[str] = Field(default_factory=list)
    physical_path: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class IisApplicationPool(BaseModel):
    name: str | None = None
    state: str | None = None
    runtime_version: str | None = None
    pipeline_mode: str | None = None
    identity_type: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class IisApplication(BaseModel):
    path: str | None = None
    site: str | None = None
    application_pool: str | None = None
    physical_path: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class IisLogFile(BaseModel):
    path: str
    length: int = 0
    last_write_time: str | None = None


class IisEvidence(BaseModel):
    source_file: str
    source_type: str = "iis_application_local"
    asset: str | None = None
    iis_detected: bool = False
    appcmd_available: bool = False
    raw_item_count: int = 0
    parsed_item_count: int = 0
    services: list[IisServiceStatus] = Field(default_factory=list)
    sites: list[IisSite] = Field(default_factory=list)
    application_pools: list[IisApplicationPool] = Field(default_factory=list)
    applications: list[IisApplication] = Field(default_factory=list)
    path_checks: list[IisPathCheck] = Field(default_factory=list)
    log_directories: list[str] = Field(default_factory=list)
    log_files: list[IisLogFile] = Field(default_factory=list)
    event_channels: list[str] = Field(default_factory=list)
    collection_warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


def parse_iis_evidence(filename: str, content: str) -> IisEvidence:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid IIS evidence JSON: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("IIS evidence JSON must be an object")

    evidence_data = parsed.get("evidence") if isinstance(parsed.get("evidence"), dict) else parsed
    evidence_data = dict(evidence_data)
    evidence_data.setdefault("source_file", filename)

    evidence = IisEvidence.model_validate(evidence_data)

    if evidence.raw_item_count == 0 and evidence.parsed_item_count == 0:
        item_count = (
            len(evidence.services)
            + len(evidence.sites)
            + len(evidence.application_pools)
            + len(evidence.applications)
            + len(evidence.log_files)
            + len(evidence.event_channels)
        )
        evidence.raw_item_count = item_count
        evidence.parsed_item_count = item_count

    return evidence