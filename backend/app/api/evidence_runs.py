from fastapi import APIRouter, Query

from app.schemas.evidence_run import (
    EvidenceRunClearResponse,
    EvidenceRunCreateRequest,
    EvidenceRunListResponse,
    EvidenceRunRecord,
)
from app.services.evidence_run_history import (
    clear_evidence_runs,
    list_evidence_runs,
    record_evidence_run,
)


router = APIRouter(prefix="/api/runs", tags=["Evidence Run History"])


@router.get("", response_model=EvidenceRunListResponse)
def get_evidence_runs(limit: int | None = Query(default=None, ge=1, le=500)) -> EvidenceRunListResponse:
    runs = list_evidence_runs(limit=limit)
    return EvidenceRunListResponse(runs=runs, count=len(runs))


@router.post("", response_model=EvidenceRunRecord)
def create_evidence_run(request: EvidenceRunCreateRequest) -> EvidenceRunRecord:
    return record_evidence_run(request)


@router.delete("", response_model=EvidenceRunClearResponse)
def delete_evidence_runs() -> EvidenceRunClearResponse:
    previous_count = clear_evidence_runs()
    return EvidenceRunClearResponse(cleared=True, previous_count=previous_count)
