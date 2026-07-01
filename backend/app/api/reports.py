from fastapi import APIRouter, HTTPException, Response

from app.schemas.report import DnsReportRequest, EndpointReportRequest
from app.services.dns_report import build_dns_report
from app.services.endpoint_report import build_endpoint_report
from app.services.report_archive import (
    delete_archived_report,
    get_archived_report,
    list_archived_reports,
    save_archived_report,
)

router = APIRouter(prefix="/api/reports")


@router.get("/archive")
def get_report_archive() -> dict:
    return {"reports": list_archived_reports()}


@router.get("/archive/{entry_id}/open")
def open_archived_report(entry_id: str) -> Response:
    try:
        entry, content = get_archived_report(entry_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Archived report entry was not found.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archived report file was not found.")

    return Response(
        content=content,
        media_type=entry.get("content_type") or "text/plain",
        headers={
            "Content-Disposition": f'inline; filename="{entry.get("filename", "custosops-report")}"'
        },
    )


@router.get("/archive/{entry_id}/download")
def download_archived_report(entry_id: str) -> Response:
    try:
        entry, content = get_archived_report(entry_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Archived report entry was not found.")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archived report file was not found.")

    return Response(
        content=content,
        media_type=entry.get("content_type") or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{entry.get("filename", "custosops-report")}"'
        },
    )


@router.delete("/archive/{entry_id}")
def delete_report_archive_entry(entry_id: str) -> dict:
    try:
        deleted = delete_archived_report(entry_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Archived report entry was not found.")

    return {"deleted": True, "entry": deleted}


@router.post("/endpoint")
def create_endpoint_report(request: EndpointReportRequest) -> dict:
    response = build_endpoint_report(
        evidence=request.evidence,
        findings=request.findings,
        report_format=request.format,
    )

    payload = response.model_dump()

    if request.archive:
        entry = save_archived_report(
            report_type="endpoint",
            report_format=response.format,
            filename=response.filename,
            content_type=response.content_type,
            content=response.content,
        )
        payload["archived"] = True
        payload["archived_path"] = entry["relative_path"]
        payload["archive_entry_id"] = entry["id"]

    return payload


@router.post("/dns")
def create_dns_report(request: DnsReportRequest) -> dict:
    response = build_dns_report(
        evidence=request.evidence,
        findings=request.findings,
        report_format=request.format,
    )

    payload = response.model_dump()

    if request.archive:
        entry = save_archived_report(
            report_type="dns",
            report_format=response.format,
            filename=response.filename,
            content_type=response.content_type,
            content=response.content,
        )
        payload["archived"] = True
        payload["archived_path"] = entry["relative_path"]
        payload["archive_entry_id"] = entry["id"]

    return payload