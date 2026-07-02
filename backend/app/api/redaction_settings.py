from fastapi import APIRouter

from app.schemas.redaction_settings import RedactionPreviewRequest, RedactionPreviewResponse, RedactionSettingsResponse, RedactionSettingsUpdateRequest
from app.services.redaction_engine import redact_text
from app.services.redaction_settings import (
    get_redaction_settings,
    reset_redaction_settings,
    save_redaction_settings,
)


router = APIRouter(prefix="/api/redaction", tags=["Redaction Settings"])


@router.get("/settings", response_model=RedactionSettingsResponse)
def get_settings() -> RedactionSettingsResponse:
    return get_redaction_settings()


@router.put("/settings", response_model=RedactionSettingsResponse)
def update_settings(request: RedactionSettingsUpdateRequest) -> RedactionSettingsResponse:
    return save_redaction_settings(request)


@router.post("/settings/reset", response_model=RedactionSettingsResponse)
def reset_settings() -> RedactionSettingsResponse:
    return reset_redaction_settings()



@router.post("/preview", response_model=RedactionPreviewResponse)
def preview_redaction(request: RedactionPreviewRequest) -> RedactionPreviewResponse:
    redacted, applied_rules = redact_text(request.text)

    return RedactionPreviewResponse(
        original=request.text,
        redacted=redacted,
        changed=redacted != request.text,
        applied_rules=applied_rules,
    )
