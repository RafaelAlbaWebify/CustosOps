from fastapi import APIRouter

from app.schemas.finding import EvidenceItem, SecurityFinding

router = APIRouter(prefix="/api")


@router.get("/sample-findings")
def get_sample_findings() -> dict:
    findings = [
        SecurityFinding(
            finding_id="CUSTOSOPS_FOUNDATION_SAMPLE",
            title="Sample finding model is available",
            severity="info",
            confidence="high",
            category="Foundation",
            affected_asset="local-demo",
            evidence=[
                EvidenceItem(
                    source="sample",
                    key="foundation_status",
                    value="finding model loaded",
                )
            ],
            why_it_matters=(
                "CustosOps needs a stable finding structure before endpoint, DNS, "
                "identity, and M365 modules are migrated."
            ),
            limitations=[
                "This is synthetic sample evidence.",
                "No endpoint or tenant data has been collected yet.",
            ],
            safe_next_steps=[
                "Validate the backend health endpoint.",
                "Validate the frontend can display modules and sample findings.",
                "Add real collectors only after the foundation model is stable.",
            ],
            non_actions=[
                "Do not treat this as a real security finding.",
                "Do not migrate old tools until the module boundary is defined.",
            ],
        )
    ]

    return {"findings": [finding.model_dump() for finding in findings]}