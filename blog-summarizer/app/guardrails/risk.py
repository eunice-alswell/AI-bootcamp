from app.guardrails.schemas import GuardrailAction, GuardrailFinding, GuardrailReport, RiskLevel


def build_report(
    findings: list[GuardrailFinding],
    block_threshold: float,
    warn_threshold: float = 0.35,
    block: bool = True,
) -> GuardrailReport:
    score = min(1.0, sum(finding.score for finding in findings))
    risk_level = _risk_level(score)
    action: GuardrailAction = "allow"
    if score >= block_threshold and block:
        action = "block"
    elif score >= warn_threshold:
        action = "warn"

    return GuardrailReport(
        risk_level=risk_level,
        risk_score=round(score, 2),
        action=action,
        findings=findings,
    )


def _risk_level(score: float) -> RiskLevel:
    if score >= 0.7:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"
