from app.ai.types import AIResponse
from app.observability.telemetry import evaluation_hook
from app.schemas.common import RequestMetadata, ResponseMetadata
from app.schemas.summarization import BlogSummaryOutput, SummarizationResponse
from app.validation.output_validator import AIOutputValidator
from app.validation.schemas import ValidationReport


class SummarizationValidationService:
    def __init__(self, validator: AIOutputValidator | None = None) -> None:
        self._validator = validator or AIOutputValidator()

    def validate_ai_response(
        self,
        ai_response: AIResponse,
        article_text: str,
        request_metadata: RequestMetadata,
    ) -> tuple[SummarizationResponse | None, ValidationReport]:
        summary, report = self._validator.validate(
            raw_output=ai_response.content,
            output_schema=BlogSummaryOutput,
            source_text=article_text,
        )
        evaluation_hook.record_validation_report(
            report,
            prompt_task=ai_response.metadata.get("prompt_task"),
            prompt_version=ai_response.metadata.get("prompt_version"),
        )
        if summary is None:
            return None, report

        response = SummarizationResponse(
            data=summary,
            metadata=ResponseMetadata(
                request_id=request_metadata.request_id,
                model=ai_response.model,
                provider=ai_response.provider,
                prompt_task=ai_response.metadata.get("prompt_task"),
                prompt_version=ai_response.metadata.get("prompt_version"),
                token_usage=ai_response.usage.model_dump(),
            ),
        )
        return response, report
