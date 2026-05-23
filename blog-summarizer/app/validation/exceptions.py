from app.validation.schemas import ValidationReport


class OutputValidationError(Exception):
    def __init__(self, message: str, report: ValidationReport) -> None:
        super().__init__(message)
        self.report = report
