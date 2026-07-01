from typing import Literal

from pydantic import BaseModel

from app.schemas.dns import DnsEvidence
from app.schemas.endpoint import EndpointEvidence
from app.schemas.finding import SecurityFinding


ReportFormat = Literal["html", "markdown", "json"]


class EndpointReportRequest(BaseModel):
    evidence: EndpointEvidence
    findings: list[SecurityFinding] | None = None
    format: ReportFormat = "html"
    archive: bool = False


class DnsReportRequest(BaseModel):
    evidence: DnsEvidence
    findings: list[SecurityFinding] | None = None
    format: ReportFormat = "html"
    archive: bool = False


class EndpointReportResponse(BaseModel):
    filename: str
    format: ReportFormat
    content_type: str
    content: str
    archived: bool = False
    archived_path: str | None = None
    archive_entry_id: str | None = None


class DnsReportResponse(BaseModel):
    filename: str
    format: ReportFormat
    content_type: str
    content: str
    archived: bool = False
    archived_path: str | None = None
    archive_entry_id: str | None = None