from typing import Any

from fastapi import APIRouter, HTTPException

from app.analyzers.endpoint_security import analyze_endpoint_evidence
from app.schemas.endpoint import EndpointEvidence
from app.services.endpoint_local_collector import (
    EndpointCollectionError,
    collect_local_endpoint_evidence,
)
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


@router.post("/collect-local")
def collect_local_endpoint_evidence_payload() -> dict:
    try:
        collected = collect_local_endpoint_evidence()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except EndpointCollectionError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected endpoint collection error: {exc}")

    evidence = EndpointEvidence.model_validate(collected["evidence"])
    findings = analyze_endpoint_evidence(evidence)

    return {
        "input_type": "local_endpoint_collection",
        "output_path": collected["relative_output_path"],
        "evidence": evidence.model_dump(),
        "findings": [finding.model_dump() for finding in findings],
    }