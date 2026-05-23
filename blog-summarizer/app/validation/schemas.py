from typing import Any, Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal["low", "medium", "high"]
RiskLevel = Literal["low", "medium", "high"]
ValidationSeverity = Literal["info", "warning", "error"]


class ValidationIssue(BaseModel):
    code: str
    severity: ValidationSeverity
    message: str
    field: str | None = None


class JsonRepairReport(BaseModel):
    attempted: bool = False
    repaired: bool = False
    strategy: str | None = None
    error: str | None = None


class ConfidenceScore(BaseModel):
    label: ConfidenceLevel
    score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class CompletenessReport(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    missing_fields: list[str] = Field(default_factory=list)
    weak_fields: list[str] = Field(default_factory=list)


class HallucinationRisk(BaseModel):
    level: RiskLevel
    score: float = Field(ge=0.0, le=1.0)
    flags: list[str] = Field(default_factory=list)


class ToxicityReport(BaseModel):
    level: RiskLevel
    score: float = Field(ge=0.0, le=1.0)
    matched_terms: list[str] = Field(default_factory=list)


class RiskAnalysisReport(BaseModel):
    hallucination: HallucinationRisk
    toxicity: ToxicityReport


class ValidationReport(BaseModel):
    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    json_repair: JsonRepairReport = Field(default_factory=JsonRepairReport)
    completeness: CompletenessReport
    confidence: ConfidenceScore
    risk: RiskAnalysisReport
    raw_output_preview: str
    parsed_output: dict[str, Any] | None = None
