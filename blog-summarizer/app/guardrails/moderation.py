from app.guardrails.detectors import detect_toxic_content
from app.guardrails.schemas import GuardrailFinding


class ContentModerationHook:
    async def check_text(self, text: str) -> list[GuardrailFinding]:
        return detect_toxic_content(text)
