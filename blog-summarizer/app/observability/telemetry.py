import logging
from time import perf_counter
from typing import Any

from app.ai.types import AIResponse, ModelConfig
from app.observability.metrics import metrics
from app.validation.schemas import ValidationReport

logger = logging.getLogger(__name__)


class AITelemetry:
    def start_timer(self) -> float:
        return perf_counter()

    def record_success(
        self,
        start_time: float,
        config: ModelConfig,
        response: AIResponse,
        attempt: int,
    ) -> None:
        latency_ms = (perf_counter() - start_time) * 1000
        labels = {
            "provider": response.provider,
            "model": response.model,
            "prompt_task": response.metadata.get("prompt_task", "unknown"),
            "prompt_version": response.metadata.get("prompt_version", "unknown"),
        }
        metrics.increment("ai.requests.success", **labels)
        metrics.observe_ms("ai.latency", latency_ms, **labels)
        metrics.increment("ai.tokens.prompt", response.usage.prompt_tokens, **labels)
        metrics.increment("ai.tokens.completion", response.usage.completion_tokens, **labels)
        metrics.increment("ai.tokens.total", response.usage.total_tokens, **labels)

        logger.info(
            "ai.request.success",
            extra={
                **labels,
                "latency_ms": round(latency_ms, 2),
                "attempt": attempt,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
                "finish_reason": response.finish_reason,
                "response_id": response.raw_response_id,
                "configured_provider": config.provider,
                "configured_model": config.model,
            },
        )

    def record_retry(self, config: ModelConfig, attempt: int, error: Exception, delay: float) -> None:
        metrics.increment("ai.requests.retry", provider=config.provider, model=config.model)
        logger.warning(
            "ai.request.retry",
            extra={
                "provider": config.provider,
                "model": config.model,
                "attempt": attempt,
                "delay": delay,
                "error_type": type(error).__name__,
            },
        )

    def record_failure(self, config: ModelConfig, error: Exception, attempts: int) -> None:
        metrics.increment("ai.requests.failure", provider=config.provider, model=config.model)
        logger.error(
            "ai.request.failure",
            extra={
                "provider": config.provider,
                "model": config.model,
                "attempts": attempts,
                "error_type": type(error).__name__,
            },
        )


class EvaluationHook:
    def record_validation_report(self, report: ValidationReport, **labels: Any) -> None:
        label_values = {
            "prompt_task": labels.get("prompt_task", "unknown"),
            "prompt_version": labels.get("prompt_version", "unknown"),
        }
        if report.valid:
            metrics.increment("ai.validation.success", **label_values)
        else:
            metrics.increment("ai.validation.failure", **label_values)

        metrics.set_gauge("ai.quality.confidence_score", report.confidence.score, **label_values)
        metrics.set_gauge("ai.quality.completeness_score", report.completeness.score, **label_values)
        metrics.set_gauge(
            "ai.quality.hallucination_score",
            report.risk.hallucination.score,
            **label_values,
        )
        metrics.set_gauge("ai.quality.toxicity_score", report.risk.toxicity.score, **label_values)

        logger.info(
            "ai.validation.evaluated",
            extra={
                **label_values,
                "valid": report.valid,
                "confidence_label": report.confidence.label,
                "confidence_score": report.confidence.score,
                "completeness_score": report.completeness.score,
                "hallucination_risk": report.risk.hallucination.level,
                "toxicity_risk": report.risk.toxicity.level,
                "issue_count": len(report.issues),
            },
        )


ai_telemetry = AITelemetry()
evaluation_hook = EvaluationHook()
