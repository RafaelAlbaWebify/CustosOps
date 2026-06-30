from fastapi import APIRouter

from app.schemas.report import EndpointReportRequest
from app.services.endpoint_report import build_endpoint_report

router = APIRouter(prefix="/api/reports")


@router.post("/endpoint")
def create_endpoint_report(request: EndpointReportRequest) -> dict:
    response = build_endpoint_report(
        evidence=request.evidence,
        findings=request.findings,
        report_format=request.format,
    )

    return response.model_dump()