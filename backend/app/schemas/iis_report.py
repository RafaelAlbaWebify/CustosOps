from typing import Any

from pydantic import BaseModel, Field


class IisReportRequest(BaseModel):
    evidence: dict[str, Any]
    findings: list[dict[str, Any]] = Field(default_factory=list)
    format: str = "html"
    archive: bool = False