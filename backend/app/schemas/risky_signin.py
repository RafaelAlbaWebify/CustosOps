from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["none", "low", "medium", "high", "hidden", "unknown"]
RiskState = Literal[
    "none",
    "confirmed_safe",
    "remediated",
    "dismissed",
    "at_risk",
    "confirmed_compromised",
    "unknown",
]
SignInStatus = Literal["success", "failure", "interrupted", "unknown"]


class RiskySignInImportRequest(BaseModel):
    filename: str
    content: str


class SignInLocation(BaseModel):
    city: str | None = None
    state: str | None = None
    country_or_region: str | None = None


class DeviceDetail(BaseModel):
    device_id: str | None = None
    display_name: str | None = None
    operating_system: str | None = None
    browser: str | None = None
    is_managed: bool | None = None
    is_compliant: bool | None = None


class RiskySignInRecord(BaseModel):
    sign_in_id: str
    created_at: str
    user_principal_name: str
    user_display_name: str | None = None
    app_display_name: str | None = None
    ip_address: str | None = None
    location: SignInLocation = Field(default_factory=SignInLocation)
    client_app_used: str | None = None
    device_detail: DeviceDetail = Field(default_factory=DeviceDetail)
    status: SignInStatus = "unknown"
    failure_reason: str | None = None
    risk_level_aggregated: RiskLevel = "unknown"
    risk_state: RiskState = "unknown"
    conditional_access_status: str | None = None
    mfa_required: bool | None = None
    mfa_satisfied: bool | None = None
    is_interactive: bool | None = None
    risk_event_types: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class RiskySignInEvidence(BaseModel):
    source_file: str
    source_type: str = "m365_entra_signin_export"
    tenant_label: str = "synthetic-tenant"
    raw_record_count: int
    parsed_record_count: int
    records: list[RiskySignInRecord] = Field(default_factory=list)
    parser_warnings: list[str] = Field(default_factory=list)
