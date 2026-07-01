from typing import Any, Literal

from pydantic import BaseModel, Field


class ExecutiveModuleInput(BaseModel):
    module_id: str
    module_name: str
    source: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    findings: list[dict[str, Any]] = Field(default_factory=list)


class ExecutiveSummaryReportRequest(BaseModel):
    modules: list[ExecutiveModuleInput] = Field(default_factory=list)
    format: Literal["html", "markdown", "json"] = "html"
    archive: bool = False
