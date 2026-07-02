import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, HTTPException

from app.analyzers.windows_event_evidence import analyze_windows_event_evidence
from app.schemas.windows_event import WindowsEventImportRequest
from app.services.windows_event_parser import parse_windows_event_evidence
from app.services.windows_event_local_collector import (
    WindowsEventCollectionError,
    collect_local_windows_event_evidence,
)

router = APIRouter(prefix="/api/windows-events")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_PATH = PROJECT_ROOT / "samples" / "windows_events" / "sample-windows-events.json"




def _local_asset_name() -> str:
    return os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "local-host"


@router.post("/import")
def import_windows_events(request: WindowsEventImportRequest) -> dict:
    evidence = parse_windows_event_evidence(filename=request.filename, content=request.content)
    findings = analyze_windows_event_evidence(evidence)

    return {
        "evidence": evidence.model_dump(),
        "parsed_event_count": evidence.parsed_event_count,
        "raw_event_count": evidence.raw_event_count,
        "warnings": evidence.parser_warnings,
        "findings": findings,
    }


@router.get("/sample-findings")
def get_sample_windows_event_findings() -> dict:
    content = SAMPLE_PATH.read_text(encoding="utf-8-sig")
    evidence = parse_windows_event_evidence(filename=SAMPLE_PATH.name, content=content)
    findings = analyze_windows_event_evidence(evidence)

    return {
        "evidence": evidence.model_dump(),
        "findings": findings,
    }



@router.post("/collect-local")
def collect_local_windows_event_evidence_payload() -> dict:
    try:
        collected = collect_local_windows_event_evidence()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except WindowsEventCollectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected Windows Event collection error: {exc}")

    evidence = parse_windows_event_evidence(
        filename="local-windows-events",
        content=__import__("json").dumps(collected["evidence"]),
    )
    findings = analyze_windows_event_evidence(evidence)

    return {
        "asset": _local_asset_name(),
        "input_type": "local_windows_event_collection",
        "output_path": collected["relative_output_path"],
        "evidence": evidence.model_dump(),
        "raw_event_count": evidence.raw_event_count,
        "parsed_event_count": evidence.parsed_event_count,
        "warnings": evidence.parser_warnings,
        "findings": findings,
    }
