from app.guardrails.schemas import GuardrailReport


class GuardrailViolationError(Exception):
    def __init__(self, message: str, report: GuardrailReport) -> None:
        super().__init__(message)
        self.report = report
