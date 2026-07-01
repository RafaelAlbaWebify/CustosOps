from typing import Any
from pydantic import BaseModel, Field


class AppLogImportRequest(BaseModel):
    filename: str
    content: str


class AppLogEntry(BaseModel):
    line_number: int
    raw: str
    timestamp: str | None = None
    level: str | None = None
    source: str | None = None
    client_ip: str | None = None
    http_method: str | None = None
    path: str | None = None
    status_code: int | None = None
    latency_ms: float | None = None


class AppLogEvidence(BaseModel):
    source_file: str
    source_type: str = "application_log"
    raw_line_count: int
    parsed_entry_count: int
    entries: list[AppLogEntry] = Field(default_factory=list)
    sensitive_indicators: list[str] = Field(default_factory=list)
    parser_warnings: list[str] = Field(default_factory=list)
    api_summary: dict[str, Any] = Field(default_factory=dict)