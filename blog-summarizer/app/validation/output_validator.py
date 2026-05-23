from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.validation.checks import analyze_risk, check_completeness, score_confidence
from app.validation.exceptions import OutputValidationError
from app.validation.json_repair import parse_json_with_repair
from app.validation.schemas import (
    CompletenessReport,
    ConfidenceScore,
    HallucinationRisk,
    JsonRepairReport,
    RiskAnalysisReport,
    ToxicityReport,
    ValidationIssue,
    ValidationReport,
)

T = TypeVar("T", bound=BaseModel)


class AIOutputValidator:
    def validate(
        self,
        raw_output: str,
        output_schema: type[T],
        source_text: str,
        raise_on_error: bool = False,
    ) -> tuple[T | None, ValidationReport]:
        parsed_output, repair_report = parse_json_with_repair(raw_output)
        issues: list[ValidationIssue] = []

        if parsed_output is None:
            issues.append(
                ValidationIssue(
                    code="malformed_json",
                    severity="error",
                    message="AI output could not be parsed as a JSON object.",
                )
            )
            report = self._empty_report(raw_output, repair_report, issues)
            if raise_on_error:
                raise OutputValidationError("AI output validation failed.", report)
            return None, report

        completeness = check_completeness(parsed_output)
        issues.extend(
            ValidationIssue(
                code="missing_field",
                severity="error",
                message=f"Required field '{field}' is missing.",
                field=field,
            )
            for field in completeness.missing_fields
        )
        issues.extend(
            ValidationIssue(
                code="weak_field",
                severity="warning",
                message=f"Field '{field}' appears incomplete.",
                field=field,
            )
            for field in completeness.weak_fields
        )

        validated_output: T | None = None
        try:
            validated_output = output_schema.model_validate(parsed_output)
        except ValidationError as exc:
            issues.extend(_pydantic_issues(exc))

        confidence = score_confidence(parsed_output, completeness)
        risk = analyze_risk(parsed_output, source_text)
        issues.extend(_risk_issues(risk))

        valid = validated_output is not None and not any(issue.severity == "error" for issue in issues)
        report = ValidationReport(
            valid=valid,
            issues=issues,
            json_repair=repair_report,
            completeness=completeness,
            confidence=confidence,
            risk=risk,
            raw_output_preview=raw_output[:500],
            parsed_output=parsed_output,
        )

        if raise_on_error and not valid:
            raise OutputValidationError("AI output validation failed.", report)
        return validated_output, report

    def _empty_report(
        self,
        raw_output: str,
        repair_report: JsonRepairReport,
        issues: list[ValidationIssue],
    ) -> ValidationReport:
        return ValidationReport(
            valid=False,
            issues=issues,
            json_repair=repair_report,
            completeness=CompletenessReport(score=0.0, missing_fields=[], weak_fields=[]),
            confidence=ConfidenceScore(label="low", score=0.0, reasons=["malformed_json"]),
            risk=RiskAnalysisReport(
                hallucination=HallucinationRisk(level="low", score=0.0, flags=[]),
                toxicity=ToxicityReport(level="low", score=0.0, matched_terms=[]),
            ),
            raw_output_preview=raw_output[:500],
            parsed_output=None,
        )


def _pydantic_issues(error: ValidationError) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for item in error.errors():
        location = ".".join(str(part) for part in item.get("loc", ()))
        error_type = item.get("type", "schema_validation_error")
        issues.append(
            ValidationIssue(
                code=error_type,
                severity="error",
                message=item.get("msg", "Schema validation failed."),
                field=location or None,
            )
        )
    return issues


def _risk_issues(risk: RiskAnalysisReport) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if risk.hallucination.level != "low":
        issues.append(
            ValidationIssue(
                code="hallucination_risk",
                severity="warning",
                message="Output contains possible unsupported claims.",
            )
        )
    if risk.toxicity.level != "low":
        issues.append(
            ValidationIssue(
                code="toxicity_risk",
                severity="warning",
                message="Output contains potentially toxic language.",
            )
        )
    return issues
