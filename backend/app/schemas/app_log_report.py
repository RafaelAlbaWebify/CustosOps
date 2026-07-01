from typing import Any, Literal

from pydantic import BaseModel


class AppLogReportRequest(BaseModel):
    evidence: dict[str, Any]
    findings: list[dict[str, Any]]
    format: Literal["html", "markdown", "json"]
    archive: bool = False