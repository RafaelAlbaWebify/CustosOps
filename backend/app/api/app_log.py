from pathlib import Path

from fastapi import APIRouter

from app.analyzers.app_log_evidence import analyze_app_log_evidence
from app.schemas.app_log import AppLogImportRequest
from app.services.app_log_parser import parse_app_log

router = APIRouter(prefix="/api/app-log")

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_LOG_PATH = PROJECT_ROOT / "samples" / "app_logs" / "fastapi-api-errors.log"


@router.post("/import")
def import_app_log(request: AppLogImportRequest) -> dict:
    evidence = parse_app_log(filename=request.filename, content=request.content)
    findings = analyze_app_log_evidence(evidence)

    return {
        "evidence": evidence.model_dump(),
        "parsed_entry_count": evidence.parsed_entry_count,
        "raw_line_count": evidence.raw_line_count,
        "sensitive_indicators": evidence.sensitive_indicators,
        "warnings": evidence.parser_warnings,
        "findings": findings,
    }


@router.get("/sample-findings")
def get_sample_app_log_findings() -> dict:
    content = SAMPLE_LOG_PATH.read_text(encoding="utf-8-sig")
    evidence = parse_app_log(filename=SAMPLE_LOG_PATH.name, content=content)
    findings = analyze_app_log_evidence(evidence)

    return {
        "evidence": evidence.model_dump(),
        "findings": findings,
    }