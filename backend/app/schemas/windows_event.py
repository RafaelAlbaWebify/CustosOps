from typing import Any

from pydantic import BaseModel, Field


class WindowsEventImportRequest(BaseModel):
    filename: str
    content: str


class WindowsEventRecord(BaseModel):
    record_number: int | None = None
    timestamp: str | None = None
    provider: str | None = None
    event_id: int | None = None
    level: str | None = None
    computer: str | None = None
    log_name: str | None = None
    user: str | None = None
    message: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


class WindowsEventEvidence(BaseModel):
    source_file: str
    source_type: str = "windows_event_log"
    raw_event_count: int
    parsed_event_count: int
    events: list[WindowsEventRecord] = Field(default_factory=list)
    parser_warnings: list[str] = Field(default_factory=list)
