from app.ai.exceptions import AIError
from app.core.config import Settings, get_settings
from app.guardrails.exceptions import GuardrailViolationError
from app.pipeline.observability import PipelineObserver
from app.pipeline.stages import (
    AIExecutionStage,
    ChunkingStage,
    ContentCleaningStage,
    ExtractiveFallbackStage,
    InputGuardrailStage,
    IngestionStage,
    OutputGuardrailStage,
    PreprocessingStage,
    PromptBuildingStage,
    ResponseGenerationStage,
    TokenEstimationStage,
    ValidationScoringStage,
)
from app.pipeline.types import BlogSummarizationPipelineResult, PipelineContext
from app.schemas.summarization import SummarizationRequest
from app.validation.exceptions import OutputValidationError


class BlogSummarizationPipeline:
    def __init__(
        self,
        settings: Settings | None = None,
        observer: PipelineObserver | None = None,
        ingestion: IngestionStage | None = None,
        preprocessing: PreprocessingStage | None = None,
        cleaning: ContentCleaningStage | None = None,
        token_estimation: TokenEstimationStage | None = None,
        chunking: ChunkingStage | None = None,
        input_guardrails: InputGuardrailStage | None = None,
        prompt_building: PromptBuildingStage | None = None,
        ai_execution: AIExecutionStage | None = None,
        output_guardrails: OutputGuardrailStage | None = None,
        validation_scoring: ValidationScoringStage | None = None,
        response_generation: ResponseGenerationStage | None = None,
        extractive_fallback: ExtractiveFallbackStage | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._observer = observer or PipelineObserver()
        self._ingestion = ingestion or IngestionStage()
        self._preprocessing = preprocessing or PreprocessingStage()
        self._cleaning = cleaning or ContentCleaningStage()
        self._token_estimation = token_estimation or TokenEstimationStage()
        self._chunking = chunking or ChunkingStage(self._settings)
        self._input_guardrails = input_guardrails or InputGuardrailStage()
        self._prompt_building = prompt_building or PromptBuildingStage()
        self._ai_execution = ai_execution or AIExecutionStage(settings=self._settings)
        self._output_guardrails = output_guardrails or OutputGuardrailStage()
        self._validation_scoring = validation_scoring or ValidationScoringStage()
        self._response_generation = response_generation or ResponseGenerationStage()
        self._extractive_fallback = extractive_fallback or ExtractiveFallbackStage()

    async def run(self, request: SummarizationRequest) -> BlogSummarizationPipelineResult:
        trace = self._observer.start_trace(request.metadata.request_id)
        context = PipelineContext(request=request)

        try:
            context = await self._observer.run_stage(
                trace,
                "ingestion",
                lambda: self._ingestion.run(context),
            )
            context = await self._observer.run_stage(
                trace,
                "preprocessing",
                lambda: self._preprocessing.run(context),
            )
            context = await self._observer.run_stage(
                trace,
                "content_cleaning",
                lambda: self._cleaning.run(context),
            )
            context = await self._observer.run_stage(
                trace,
                "token_estimation",
                lambda: self._token_estimation.run(context),
            )
            context = await self._observer.run_stage(
                trace,
                "chunking",
                lambda: self._chunking.run(context),
                chunk_target_tokens=self._settings.pipeline_chunk_target_tokens,
            )
            context = await self._observer.run_stage(
                trace,
                "input_guardrails",
                lambda: self._input_guardrails.run(context),
            )
            context = await self._run_ai_path(trace, context, prompt_version=None)

            if context.validation_report and not context.validation_report.valid:
                context = await self._run_prompt_fallback(trace, context)

            context = await self._observer.run_stage(
                trace,
                "response_generation",
                lambda: self._response_generation.run(context),
            )
            trace = self._observer.finish_trace(trace)
            return BlogSummarizationPipelineResult(
                status="degraded" if context.fallback_used else "success",
                response=context.response,
                validation_report=context.validation_report,
                safety=context.safety,
                trace=trace,
                fallback_used=context.fallback_used,
            )
        except (AIError, GuardrailViolationError, OutputValidationError, ValueError):
            if not self._settings.pipeline_allow_extractive_fallback:
                trace = self._observer.finish_trace(trace)
                return BlogSummarizationPipelineResult(
                    status="failed",
                    response=context.response,
                    validation_report=context.validation_report,
                    safety=context.safety,
                    trace=trace,
                    fallback_used=context.fallback_used,
                )

            context = await self._observer.run_stage(
                trace,
                "extractive_fallback",
                lambda: self._extractive_fallback.run(context),
            )
            trace = self._observer.finish_trace(trace)
            return BlogSummarizationPipelineResult(
                status="degraded",
                response=context.response,
                validation_report=context.validation_report,
                safety=context.safety,
                trace=trace,
                fallback_used=True,
            )

    async def _run_ai_path(
        self,
        trace,
        context: PipelineContext,
        prompt_version: str | None,
    ) -> PipelineContext:
        context = await self._observer.run_stage(
            trace,
            "prompt_building",
            lambda: self._prompt_building.run(context, version=prompt_version),
            prompt_version=prompt_version or "latest",
        )
        context = await self._observer.run_stage(
            trace,
            "ai_execution",
            lambda: self._ai_execution.run(context),
        )
        context = await self._observer.run_stage(
            trace,
            "output_guardrails",
            lambda: self._output_guardrails.run(context),
        )
        return await self._observer.run_stage(
            trace,
            "validation_scoring",
            lambda: self._validation_scoring.run(context),
        )

    async def _run_prompt_fallback(self, trace, context: PipelineContext) -> PipelineContext:
        try:
            fallback_context = context.model_copy(
                update={
                    "ai_request": None,
                    "ai_response": None,
                    "validation_report": None,
                    "response": None,
                    "fallback_used": True,
                }
            )
            return await self._run_ai_path(trace, fallback_context, prompt_version="0.1.0")
        except (AIError, OutputValidationError, ValueError):
            return await self._observer.run_stage(
                trace,
                "extractive_fallback",
                lambda: self._extractive_fallback.run(context),
            )
