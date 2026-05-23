from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high"]
GuardrailAction = Literal["allow", "warn", "block", "fallback"]


class GuardrailFinding(BaseModel):
    code: str
    message: str
    score: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class GuardrailReport(BaseModel):
    risk_level: RiskLevel
    risk_score: float = Field(ge=0.0, le=1.0)
    action: GuardrailAction
    findings: list[GuardrailFinding] = Field(default_factory=list)


class SafetyAssessment(BaseModel):
    input_report: GuardrailReport | None = None
    output_report: GuardrailReport | None = None
