import re
from typing import Any

from app.validation.schemas import (
    CompletenessReport,
    ConfidenceScore,
    HallucinationRisk,
    RiskAnalysisReport,
    ToxicityReport,
)

REQUIRED_SUMMARY_FIELDS = [
    "title",
    "summary",
    "key_points",
    "audience_takeaway",
    "confidence",
]

TOXICITY_TERMS = {
    "idiot",
    "stupid",
    "hate",
    "kill",
    "worthless",
}

UNSUPPORTED_CLAIM_PATTERNS = [
    r"\b\d{4}\b",
    r"\b\d+(?:\.\d+)?%",
    r"\$\s?\d+",
    r"\b(?:study|researchers|report|survey)\b",
]


def check_completeness(parsed_output: dict[str, Any]) -> CompletenessReport:
    missing_fields = [field for field in REQUIRED_SUMMARY_FIELDS if field not in parsed_output]
    weak_fields: list[str] = []

    summary = str(parsed_output.get("summary", ""))
    key_points = parsed_output.get("key_points", [])
    audience_takeaway = str(parsed_output.get("audience_takeaway", ""))

    if len(summary.split()) < 20:
        weak_fields.append("summary")
    if not isinstance(key_points, list) or len(key_points) < 3:
        weak_fields.append("key_points")
    if len(audience_takeaway.split()) < 5:
        weak_fields.append("audience_takeaway")

    penalty = (len(missing_fields) * 0.2) + (len(weak_fields) * 0.1)
    return CompletenessReport(
        score=max(0.0, 1.0 - penalty),
        missing_fields=missing_fields,
        weak_fields=weak_fields,
    )


def score_confidence(parsed_output: dict[str, Any], completeness: CompletenessReport) -> ConfidenceScore:
    model_confidence = parsed_output.get("confidence")
    base_score = {"high": 0.9, "medium": 0.65, "low": 0.35}.get(model_confidence, 0.4)
    score = round((base_score + completeness.score) / 2, 2)
    reasons = [f"model_reported_confidence={model_confidence or 'missing'}"]
    if completeness.missing_fields:
        reasons.append("missing_required_fields")
    if completeness.weak_fields:
        reasons.append("weak_summary_fields")

    if score >= 0.75:
        label = "high"
    elif score >= 0.5:
        label = "medium"
    else:
        label = "low"

    return ConfidenceScore(label=label, score=score, reasons=reasons)


def analyze_hallucination_risk(parsed_output: dict[str, Any], source_text: str) -> HallucinationRisk:
    combined_output = " ".join(_flatten_text(parsed_output))
    flags: list[str] = []

    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
        for match in re.findall(pattern, combined_output, flags=re.IGNORECASE):
            if str(match).lower() not in source_text.lower():
                flags.append(f"unsupported_claim_indicator:{match}")

    output_entities = _extract_named_entities(combined_output)
    source_entities = _extract_named_entities(source_text)
    unsupported_entities = sorted(output_entities - source_entities)
    flags.extend(f"unsupported_entity:{entity}" for entity in unsupported_entities[:5])

    score = min(1.0, len(flags) * 0.15)
    return HallucinationRisk(level=_risk_level(score), score=round(score, 2), flags=flags[:10])


def analyze_toxicity(parsed_output: dict[str, Any]) -> ToxicityReport:
    combined_output = " ".join(_flatten_text(parsed_output)).lower()
    matched_terms = sorted(term for term in TOXICITY_TERMS if term in combined_output)
    score = min(1.0, len(matched_terms) * 0.25)
    return ToxicityReport(
        level=_risk_level(score),
        score=round(score, 2),
        matched_terms=matched_terms,
    )


def analyze_risk(parsed_output: dict[str, Any], source_text: str) -> RiskAnalysisReport:
    return RiskAnalysisReport(
        hallucination=analyze_hallucination_risk(parsed_output, source_text),
        toxicity=analyze_toxicity(parsed_output),
    )


def _flatten_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _flatten_text(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _flatten_text(item)]
    return []


def _extract_named_entities(text: str) -> set[str]:
    candidates = re.findall(r"\b[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*)+\b|\b[A-Z]{2,}\b", text)
    return {candidate.strip() for candidate in candidates}


def _risk_level(score: float) -> str:
    if score >= 0.6:
        return "high"
    if score >= 0.25:
        return "medium"
    return "low"
