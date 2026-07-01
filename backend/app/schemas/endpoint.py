from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EndpointEvidence(BaseModel):
    model_config = ConfigDict(extra="allow")
    schema_version: str = "custosops.endpoint.v0.1"
    collected_at: str | None = None
    collector: str | None = None
    collector_mode: str | None = None
    computer: dict[str, Any] = Field(default_factory=dict)
    operating_system: dict[str, Any] = Field(default_factory=dict)
    firmware: dict[str, Any] = Field(default_factory=dict)
    encryption: dict[str, Any] = Field(default_factory=dict)
    protection: dict[str, Any] = Field(default_factory=dict)
    access_surface: dict[str, Any] = Field(default_factory=dict)
    maintenance: dict[str, Any] = Field(default_factory=dict)
    software: dict[str, Any] = Field(default_factory=dict)
    safety: dict[str, Any] = Field(default_factory=dict)