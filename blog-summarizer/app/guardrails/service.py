from app.core.config import Settings, get_settings
from app.guardrails.detectors import (
    detect_malicious_input,
    detect_prompt_injection,
    detect_token_abuse,
)
from app.guardrails.exceptions import GuardrailViolationError
from app.guardrails.moderation import ContentModerationHook
from app.guardrails.risk import build_report
from app.guardrails.schemas import GuardrailReport


class RequestProtectionService:
    def __init__(
        self,
        settings: Settings | None = None,
        moderation: ContentModerationHook | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._moderation = moderation or ContentModerationHook()

    async def assess_input(self, text: str, estimated_tokens: int | None = None) -> GuardrailReport:
        findings = []
        findings.extend(detect_prompt_injection(text))
        findings.extend(detect_malicious_input(text))
        findings.extend(await self._moderation.check_text(text))
        if estimated_tokens is not None:
            findings.extend(
                detect_token_abuse(
                    estimated_tokens=estimated_tokens,
                    max_tokens=self._settings.pipeline_max_article_tokens,
                )
            )

        return build_report(
            findings=findings,
            block_threshold=min(
                self._settings.security_prompt_injection_threshold,
                self._settings.security_malicious_input_threshold,
            ),
            block=self._settings.security_block_high_risk_input,
        )

    async def enforce_input(self, text: str, estimated_tokens: int | None = None) -> GuardrailReport:
        report = await self.assess_input(text=text, estimated_tokens=estimated_tokens)
        if report.action == "block":
            raise GuardrailViolationError("Input failed AI guardrail checks.", report)
        return report


class AISafetyService:
    def __init__(
        self,
        settings: Settings | None = None,
        moderation: ContentModerationHook | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._moderation = moderation or ContentModerationHook()

    async def assess_output(self, text: str) -> GuardrailReport:
        findings = []
        findings.extend(detect_prompt_injection(text))
        findings.extend(await self._moderation.check_text(text))
        return build_report(
            findings=findings,
            block_threshold=0.7,
            block=self._settings.security_block_high_risk_output,
        )

    async def enforce_output(self, text: str) -> GuardrailReport:
        report = await self.assess_output(text)
        if report.action == "block":
            raise GuardrailViolationError("AI output failed safety checks.", report)
        return report
