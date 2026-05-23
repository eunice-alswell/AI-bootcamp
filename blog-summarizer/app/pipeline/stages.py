import html
import json
import re

from app.ai.client import AIClientManager, get_ai_client_manager
from app.ai.exceptions import AIRetryableProviderError
from app.ai.types import AIResponse, TokenUsage
from app.core.config import Settings, get_settings
from app.guardrails.exceptions import GuardrailViolationError
from app.guardrails.service import AISafetyService, RequestProtectionService
from app.observability.telemetry import evaluation_hook
from app.pipeline.retry import retry_async
from app.pipeline.types import BlogDocument, ContentChunk, PipelineContext, TokenEstimate
from app.prompts.builder import PromptBuilder
from app.schemas.common import ResponseMetadata
from app.schemas.summarization import BlogSummaryOutput, SummarizationResponse
from app.services.summarization import SummarizationValidationService
from app.validation.output_validator import AIOutputValidator


class IngestionStage:
    async def run(self, context: PipelineContext) -> PipelineContext:
        request = context.request
        context.document = BlogDocument(
            text=request.article_text,
            source_url=str(request.source_url) if request.source_url else None,
            metadata={"request_id": request.metadata.request_id},
        )
        return context


class PreprocessingStage:
    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.document is None:
            raise ValueError("Document is required before preprocessing.")
        text = html.unescape(context.document.text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        context.document = context.document.model_copy(update={"text": text.strip()})
        return context


class ContentCleaningStage:
    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.document is None:
            raise ValueError("Document is required before cleaning.")
        text = re.sub(r"<[^>]+>", " ", context.document.text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        context.cleaned_text = text.strip()
        return context


class TokenEstimationStage:
    async def run(self, context: PipelineContext) -> PipelineContext:
        text = context.cleaned_text or ""
        words = len(text.split())
        context.token_estimate = TokenEstimate(
            characters=len(text),
            words=words,
            estimated_tokens=max(1, int(words * 1.3)),
        )
        return context


class ChunkingStage:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    async def run(self, context: PipelineContext) -> PipelineContext:
        text = context.cleaned_text or ""
        words = text.split()
        target_words = max(100, int(self._settings.pipeline_chunk_target_tokens / 1.3))
        overlap_words = max(0, int(self._settings.pipeline_chunk_overlap_tokens / 1.3))
        step = max(1, target_words - overlap_words)

        chunks: list[ContentChunk] = []
        for index, start in enumerate(range(0, len(words), step)):
            chunk_words = words[start : start + target_words]
            if not chunk_words:
                break
            chunk_text = " ".join(chunk_words)
            chunks.append(
                ContentChunk(
                    index=index,
                    text=chunk_text,
                    estimated_tokens=max(1, int(len(chunk_words) * 1.3)),
                )
            )
            if start + target_words >= len(words):
                break

        context.chunks = chunks or [ContentChunk(index=0, text=text, estimated_tokens=1)]
        return context


class InputGuardrailStage:
    def __init__(self, service: RequestProtectionService | None = None) -> None:
        self._service = service or RequestProtectionService()

    async def run(self, context: PipelineContext) -> PipelineContext:
        report = await self._service.assess_input(
            text=context.cleaned_text or context.request.article_text,
            estimated_tokens=context.token_estimate.estimated_tokens
            if context.token_estimate
            else None,
        )
        context.safety.input_report = report
        if report.action == "block":
            raise GuardrailViolationError("Input failed AI guardrail checks.", report)
        return context


class PromptBuildingStage:
    def __init__(self, builder: PromptBuilder | None = None) -> None:
        self._builder = builder or PromptBuilder()

    async def run(self, context: PipelineContext, version: str | None = None) -> PipelineContext:
        request = context.request
        article_text = _join_chunks(context.chunks)
        context.ai_request = self._builder.build_ai_request(
            task="summarization.blog",
            version=version,
            variables={
                "article_text": article_text,
                "audience": request.audience,
                "tone": request.tone,
                "summary_length": request.summary_length,
                "focus_area": request.focus_area,
            },
        )
        return context


class AIExecutionStage:
    def __init__(
        self,
        ai_client: AIClientManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._ai_client = ai_client or get_ai_client_manager()
        self._settings = settings or get_settings()

    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.ai_request is None:
            raise ValueError("AI request is required before execution.")

        context.ai_response = await retry_async(
            operation=lambda: self._ai_client.generate(context.ai_request),
            attempts=self._settings.ai_max_retries + 1,
            backoff_seconds=self._settings.ai_retry_backoff_seconds,
            retryable_exceptions=(AIRetryableProviderError,),
        )
        return context


class ValidationScoringStage:
    def __init__(self, service: SummarizationValidationService | None = None) -> None:
        self._service = service or SummarizationValidationService()

    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.ai_response is None:
            raise ValueError("AI response is required before validation.")
        response, report = self._service.validate_ai_response(
            ai_response=context.ai_response,
            article_text=context.cleaned_text or "",
            request_metadata=context.request.metadata,
        )
        context.response = response
        context.validation_report = report
        return context


class OutputGuardrailStage:
    def __init__(self, service: AISafetyService | None = None) -> None:
        self._service = service or AISafetyService()

    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.ai_response is None:
            raise ValueError("AI response is required before output guardrails.")
        report = await self._service.enforce_output(context.ai_response.content)
        context.safety.output_report = report
        return context


class ResponseGenerationStage:
    async def run(self, context: PipelineContext) -> PipelineContext:
        if context.response is not None:
            return context
        if context.validation_report is not None and not context.validation_report.valid:
            raise ValueError("Validated AI output is not suitable for response generation.")
        raise ValueError("Pipeline completed without a response.")


class ExtractiveFallbackStage:
    def __init__(
        self,
        validator: AIOutputValidator | None = None,
        safety_service: AISafetyService | None = None,
    ) -> None:
        self._validator = validator or AIOutputValidator()
        self._safety_service = safety_service or AISafetyService()

    async def run(self, context: PipelineContext) -> PipelineContext:
        source_text = context.cleaned_text or context.request.article_text
        sentences = _sentences(source_text)
        summary_text = " ".join(sentences[:3]) or source_text[:500]
        key_points = [sentence[:220] for sentence in sentences[:5]]
        while len(key_points) < 3:
            key_points.append("The source article did not contain enough distinct points.")

        output = BlogSummaryOutput(
            title="Fallback summary",
            summary=summary_text,
            key_points=key_points[:5],
            audience_takeaway="Review the original article before making decisions from this fallback summary.",
            confidence="low",
        )
        raw_output = json.dumps(output.model_dump())
        ai_response = AIResponse(
            provider="groq",
            model="extractive-fallback",
            content=raw_output,
            usage=TokenUsage(),
            metadata={
                "prompt_task": "summarization.blog",
                "prompt_version": "extractive-fallback",
            },
        )
        _, context.validation_report = self._validator.validate(
            raw_output=raw_output,
            output_schema=BlogSummaryOutput,
            source_text=source_text,
        )
        evaluation_hook.record_validation_report(
            context.validation_report,
            prompt_task="summarization.blog",
            prompt_version="extractive-fallback",
        )
        context.fallback_used = True
        context.ai_response = ai_response
        context.response = SummarizationResponse(
            data=output,
            metadata=ResponseMetadata(
                request_id=context.request.metadata.request_id,
                model=ai_response.model,
                provider="fallback",
                prompt_task="summarization.blog",
                prompt_version="extractive-fallback",
                token_usage=ai_response.usage.model_dump(),
            ),
        )
        if context.safety.output_report is None:
            context.safety.output_report = await self._safety_service.assess_output(raw_output)
        return context


def _join_chunks(chunks: list[ContentChunk]) -> str:
    return "\n\n".join(f"[Chunk {chunk.index + 1}]\n{chunk.text}" for chunk in chunks)


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
