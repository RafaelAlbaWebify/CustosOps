from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["info", "low", "medium", "high", "critical"]
Confidence = Literal["low", "medium", "high"]
FindingStatus = Literal["open", "verify", "accepted", "fixed", "not_applicable"]


class EvidenceItem(BaseModel):
    source: str
    key: str
    value: str


class SecurityFinding(BaseModel):
    finding_id: str
    title: str
    severity: Severity
    confidence: Confidence
    category: str
    affected_asset: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    why_it_matters: str
    limitations: list[str] = Field(default_factory=list)
    safe_next_steps: list[str] = Field(default_factory=list)
    non_actions: list[str] = Field(default_factory=list)
    status: FindingStatus = "open"