import json
import os

from fastapi import APIRouter, HTTPException

from app.analyzers.iis_evidence import analyze_iis_evidence
from app.schemas.iis import IisImportRequest, parse_iis_evidence
from app.services.iis_local_collector import collect_local_iis_evidence

router = APIRouter(prefix="/api/iis")


def _local_asset_name() -> str:
    return os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "local-host"


@router.post("/import")
def import_iis_evidence(request: IisImportRequest) -> dict:
    try:
        evidence = parse_iis_evidence(filename=request.filename, content=request.content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    findings = analyze_iis_evidence(evidence)

    return {
        "asset": evidence.asset or _local_asset_name(),
        "input_type": "iis_application_import",
        "evidence": evidence.model_dump(),
        "raw_item_count": evidence.raw_item_count,
        "parsed_item_count": evidence.parsed_item_count,
        "warnings": evidence.collection_warnings,
        "findings": findings,
    }


@router.post("/collect-local")
def collect_local_iis_evidence_payload() -> dict:
    try:
        evidence = collect_local_iis_evidence()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected IIS/Application collection error: {exc}")

    findings = analyze_iis_evidence(evidence)

    return {
        "asset": evidence.asset or _local_asset_name(),
        "input_type": "local_iis_application_collection",
        "evidence": evidence.model_dump(),
        "raw_item_count": evidence.raw_item_count,
        "parsed_item_count": evidence.parsed_item_count,
        "warnings": evidence.collection_warnings,
        "findings": findings,
    }


@router.get("/sample-findings")
def get_sample_iis_findings() -> dict:
    evidence = parse_iis_evidence(
        filename="sample-iis-application-evidence.json",
        content=json.dumps(
            {
                "source_file": "sample-iis-application-evidence.json",
                "asset": "sample-web-01",
                "iis_detected": True,
                "appcmd_available": True,
                "raw_item_count": 4,
                "parsed_item_count": 4,
                "services": [
                    {"name": "W3SVC", "display_name": "World Wide Web Publishing Service", "status": "Stopped", "start_type": "Automatic"}
                ],
                "sites": [
                    {"name": "Default Web Site", "state": "Stopped", "bindings": ["http/*:80:"]}
                ],
                "application_pools": [
                    {"name": "DefaultAppPool", "state": "Stopped", "runtime_version": "v4.0"}
                ],
                "applications": [
                    {"path": "/", "site": "Default Web Site", "application_pool": "DefaultAppPool"}
                ],
                "log_files": [],
                "collection_warnings": ["Sample evidence for IIS/Application module."],
            }
        ),
    )
    findings = analyze_iis_evidence(evidence)

    return {
        "evidence": evidence.model_dump(),
        "findings": findings,
    }