from typing import Any

from fastapi import APIRouter

from app.analyzers.risky_signin_evidence import analyze_risky_signin_evidence
from app.schemas.risky_signin import RiskySignInEvidence, RiskySignInImportRequest
from app.services.sample_loader import load_sample_json


router = APIRouter(prefix="/api/risky-signins")


@router.get("/sample-evidence")
def get_sample_risky_signin_evidence() -> dict:
    return load_sample_json("samples/risky_signins/sample-risky-signins.json")


@router.get("/sample-findings")
def get_sample_risky_signin_findings() -> dict:
    raw = load_sample_json("samples/risky_signins/sample-risky-signins.json")
    evidence = RiskySignInEvidence.model_validate(raw)
    findings = analyze_risky_signin_evidence(evidence)

    return {
        "evidence": evidence.model_dump(),
        "findings": [finding.model_dump() for finding in findings],
    }


@router.post("/import")
def import_risky_signins(request: RiskySignInImportRequest) -> dict:
    evidence = RiskySignInEvidence.model_validate_json(request.content)
    findings = analyze_risky_signin_evidence(evidence)

    return {
        "input_type": "risky_signin_import",
        "source_file": request.filename,
        "evidence": evidence.model_dump(),
        "raw_record_count": evidence.raw_record_count,
        "parsed_record_count": evidence.parsed_record_count,
        "warnings": evidence.parser_warnings,
        "findings": [finding.model_dump() for finding in findings],
    }


@router.post("/analyze")
def analyze_risky_signin_payload(payload: dict[str, Any]) -> dict:
    input_type = "risky_signin_evidence"

    if isinstance(payload.get("evidence"), dict):
        raw_evidence = payload["evidence"]
        input_type = "risky_signin_report_json"
    else:
        raw_evidence = payload

    evidence = RiskySignInEvidence.model_validate(raw_evidence)
    findings = analyze_risky_signin_evidence(evidence)

    return {
        "input_type": input_type,
        "findings": [finding.model_dump() for finding in findings],
    }
