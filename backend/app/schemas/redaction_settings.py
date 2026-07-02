from typing import Literal

from pydantic import BaseModel, Field


RedactionRuleKind = Literal["field", "pattern", "literal"]


class RedactionRule(BaseModel):
    rule_id: str
    label: str
    kind: RedactionRuleKind
    value: str
    enabled: bool = True
    replacement: str = "[REDACTED]"
    description: str | None = None


class RedactionSettingsUpdateRequest(BaseModel):
    enabled: bool = True
    profile_name: str = "default-local"
    rules: list[RedactionRule] = Field(default_factory=list)


class RedactionSettingsResponse(RedactionSettingsUpdateRequest):
    updated_at: str
