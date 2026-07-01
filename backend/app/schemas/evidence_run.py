from typing import Any, Literal

from pydantic import BaseModel, Field


EvidenceRunStatus = Literal["success", "warning", "failed"]


class EvidenceRunCreateRequest(BaseModel):
    module_id: str
    module_name: str
    source: str = "unknown"
    source_type: str = "unknown"
    asset: str = "unknown"
    status: EvidenceRunStatus = "success"
    raw_count: int = 0
    parsed_count: int = 0
    finding_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    warning_count: int = 0
    report_ids: list[str] = Field(default_factory=list)
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceRunRecord(EvidenceRunCreateRequest):
    run_id: str
    created_at: str


class EvidenceRunListResponse(BaseModel):
    runs: list[EvidenceRunRecord]
    count: int


class EvidenceRunClearResponse(BaseModel):
    cleared: bool
    previous_count: int
