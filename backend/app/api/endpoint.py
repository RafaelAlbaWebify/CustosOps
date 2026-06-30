from typing import Any

from fastapi import APIRouter

from app.analyzers.endpoint_security import analyze_endpoint_evidence
from app.schemas.endpoint import EndpointEvidence
from app.services.sample_loader import load_sample_json

router = APIRouter(prefix="/api/endpoint")


@router.get("/sample-evidence")
def get_sample_endpoint_evidence() -> dict:
    return load_sample_json("samples/endpoint/sample-endpoint-evidence.json")


@router.get("/sample-findings")
def get_sample_endpoint_findings() -> dict:
    raw = load_sample_json("samples/endpoint/sample-endpoint-evidence.json")
    evidence = EndpointEvidence.model_validate(raw)
    findings = analyze_endpoint_evidence(evidence)

    return {"findings": [finding.model_dump() for finding in findings]}


@router.post("/analyze")
def analyze_endpoint_evidence_payload(payload: dict[str, Any]) -> dict:
    input_type = "endpoint_evidence"

    if isinstance(payload.get("evidence"), dict):
        raw_evidence = payload["evidence"]
        input_type = "endpoint_report_json"
    else:
        raw_evidence = payload

    evidence = EndpointEvidence.model_validate(raw_evidence)
    findings = analyze_endpoint_evidence(evidence)

    return {
        "input_type": input_type,
        "findings": [finding.model_dump() for finding in findings],
    }