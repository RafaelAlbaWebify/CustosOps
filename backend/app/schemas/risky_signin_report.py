from typing import Any, Literal

from pydantic import BaseModel, Field


class RiskySignInReportRequest(BaseModel):
    evidence: dict[str, Any]
    findings: list[dict[str, Any]] = Field(default_factory=list)
    format: Literal["html", "markdown", "json"] = "html"
    archive: bool = False
