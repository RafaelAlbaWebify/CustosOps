from fastapi import APIRouter

from app.analyzers.dns_hygiene import analyze_dns_evidence
from app.schemas.dns import DnsEvidence
from app.services.sample_loader import load_sample_json

router = APIRouter(prefix="/api/dns")


@router.get("/sample-evidence")
def get_sample_dns_evidence() -> dict:
    return load_sample_json("samples/dns/sample-dns-evidence.json")


@router.get("/sample-findings")
def get_sample_dns_findings() -> dict:
    raw = load_sample_json("samples/dns/sample-dns-evidence.json")
    evidence = DnsEvidence.model_validate(raw)
    findings = analyze_dns_evidence(evidence)

    return {"findings": [finding.model_dump() for finding in findings]}


@router.post("/analyze")
def analyze_dns_evidence_payload(evidence: DnsEvidence) -> dict:
    findings = analyze_dns_evidence(evidence)

    return {"findings": [finding.model_dump() for finding in findings]}