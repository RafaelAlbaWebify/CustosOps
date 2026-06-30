from typing import Literal

from pydantic import BaseModel

from app.schemas.endpoint import EndpointEvidence
from app.schemas.finding import SecurityFinding


ReportFormat = Literal["html", "markdown", "json"]


class EndpointReportRequest(BaseModel):
    evidence: EndpointEvidence
    findings: list[SecurityFinding] | None = None
    format: ReportFormat = "html"


class EndpointReportResponse(BaseModel):
    filename: str
    format: ReportFormat
    content_type: str
    content: str