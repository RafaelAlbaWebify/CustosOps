import json
from fastapi import APIRouter, HTTPException, Response

from app.schemas.app_log_report import AppLogReportRequest
from app.schemas.report import DnsReportRequest, EndpointReportRequest
from app.schemas.executive_summary_report import ExecutiveSummaryReportRequest
from app.schemas.windows_event_report import WindowsEventReportRequest
from app.schemas.iis_report import IisReportRequest
from app.services.app_log_report import build_app_log_report
from app.services.dns_report import build_dns_report
from app.services.endpoint_report import build_endpoint_report
from app.services.windows_event_report import build_windows_event_report
from app.services.iis_report import build_iis_report
from app.services.executive_summary_report import build_executive_summary_report
from app.services.redaction_engine import redact_text
from app.services.redaction_settings import get_redaction_settings
from app.services.report_archive import (
    delete_archived_report,
    get_archived_report,
    list_archived_reports,
    save_archived_report,
)



def _merge_rule_ids(target: list[str], source: list[str]) -> None:
    for rule_id in source:
        if rule_id not in target:
            target.append(rule_id)


def _redact_report_value(value: object, settings) -> tuple[object, list[str]]:
    if isinstance(value, str):
        return redact_text(value, settings=settings)

    if isinstance(value, list):
        redacted_items = []
        applied_rules: list[str] = []

        for item in value:
            redacted_item, item_rules = _redact_report_value(item, settings)
            redacted_items.append(redacted_item)
            _merge_rule_ids(applied_rules, item_rules)

        return redacted_items, applied_rules

    if isinstance(value, dict):
        redacted_dict = {}
        applied_rules: list[str] = []

        for key, item in value.items():
            redacted_item, item_rules = _redact_report_value(item, settings)
            redacted_dict[key] = redacted_item
            _merge_rule_ids(applied_rules, item_rules)

        return redacted_dict, applied_rules

    return value, []


def _apply_report_redaction(payload: dict) -> dict:
    content = payload.get("content")
    settings = get_redaction_settings()

    if not isinstance(content, str):
        payload["redaction"] = {
            "enabled": settings.enabled,
            "profile_name": settings.profile_name,
            "changed": False,
            "applied_rules": [],
        }
        return payload

    original = content
    applied_rules: list[str] = []

    if str(payload.get("format", "")).lower() == "json":
        try:
            parsed = json.loads(content)
            redacted_value, applied_rules = _redact_report_value(parsed, settings)
            redacted = json.dumps(redacted_value, indent=2)
        except Exception:
            redacted, applied_rules = redact_text(content, settings=settings)
    else:
        redacted, applied_rules = redact_text(content, settings=settings)

    payload["content"] = redacted
    payload["redaction"] = {
        "enabled": settings.enabled,
        "profile_name": settings.profile_name,
        "changed": redacted != original,
        "applied_rules": applied_rules,
    }

    return payload


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

    payload = _apply_report_redaction(response.model_dump())

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

    payload = _apply_report_redaction(response.model_dump())

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


@router.post("/app-log")
def create_app_log_report(request: AppLogReportRequest) -> dict:
    response = build_app_log_report(
        evidence=request.evidence,
        findings=request.findings,
        report_format=request.format,
    )

    payload = _apply_report_redaction(response.model_dump())

    if request.archive:
        entry = save_archived_report(
            report_type="app_log",
            report_format=response.format,
            filename=response.filename,
            content_type=response.content_type,
            content=response.content,
        )
        payload["archived"] = True
        payload["archived_path"] = entry["relative_path"]
        payload["archive_entry_id"] = entry["id"]

    return payload


@router.post("/windows-events")
def create_windows_event_report(request: WindowsEventReportRequest) -> dict:
    response = build_windows_event_report(
        evidence=request.evidence,
        findings=request.findings,
        report_format=request.format,
    )

    payload = _apply_report_redaction(response.model_dump())

    if request.archive:
        entry = save_archived_report(
            report_type="windows_events",
            report_format=response.format,
            filename=response.filename,
            content_type=response.content_type,
            content=response.content,
        )
        payload["archived"] = True
        payload["archived_path"] = entry["relative_path"]
        payload["archive_entry_id"] = entry["id"]

    return payload




@router.post("/iis")
def create_iis_report(request: IisReportRequest) -> dict:
    response = build_iis_report(
        evidence=request.evidence,
        findings=request.findings,
        report_format=request.format,
    )

    payload = _apply_report_redaction(response.model_dump())

    if request.archive:
        entry = save_archived_report(
            report_type="iis",
            report_format=response.format,
            filename=response.filename,
            content_type=response.content_type,
            content=response.content,
        )
        payload["archived"] = True
        payload["archived_path"] = entry["relative_path"]
        payload["archive_entry_id"] = entry["id"]
    else:
        payload["archived"] = False
        payload["archive_entry_id"] = None

    return payload
@router.post("/executive-summary")
def create_executive_summary_report(request: ExecutiveSummaryReportRequest) -> dict:
    response = build_executive_summary_report(
        modules=[module.model_dump() for module in request.modules],
        report_format=request.format,
    )

    payload = _apply_report_redaction(response.model_dump())

    if request.archive:
        entry = save_archived_report(
            report_type="executive_summary",
            report_format=response.format,
            filename=response.filename,
            content_type=response.content_type,
            content=response.content,
        )
        payload["archived"] = True
        payload["archived_path"] = entry["relative_path"]
        payload["archive_entry_id"] = entry["id"]

    return payload
