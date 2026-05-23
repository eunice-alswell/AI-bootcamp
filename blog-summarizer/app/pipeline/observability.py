import logging
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

from app.observability.metrics import metrics
from app.pipeline.types import PipelineStageTrace, PipelineTrace

logger = logging.getLogger(__name__)


class PipelineObserver:
    def start_trace(self, request_id: str) -> PipelineTrace:
        logger.info("pipeline.started", extra={"request_id": request_id})
        return PipelineTrace(request_id=request_id)

    def finish_trace(self, trace: PipelineTrace) -> PipelineTrace:
        finished_at = datetime.now(UTC)
        duration_ms = (finished_at - trace.started_at).total_seconds() * 1000
        logger.info(
            "pipeline.finished",
            extra={"request_id": trace.request_id, "duration_ms": round(duration_ms, 2)},
        )
        metrics.observe_ms("pipeline.duration", duration_ms)
        return trace.model_copy(update={"finished_at": finished_at, "duration_ms": duration_ms})

    async def run_stage(self, trace: PipelineTrace, name: str, operation, **metadata: Any):
        started_at = datetime.now(UTC)
        start_time = perf_counter()
        logger.info(
            "pipeline.stage.started",
            extra={"request_id": trace.request_id, "stage": name, **metadata},
        )
        stage_trace = PipelineStageTrace(name=name, started_at=started_at, metadata=metadata)

        try:
            result = await operation()
            duration_ms = (perf_counter() - start_time) * 1000
            trace.stages.append(
                stage_trace.model_copy(
                    update={
                        "finished_at": datetime.now(UTC),
                        "duration_ms": duration_ms,
                        "status": "success",
                    }
                )
            )
            logger.info(
                "pipeline.stage.finished",
                extra={
                    "request_id": trace.request_id,
                    "stage": name,
                    "duration_ms": round(duration_ms, 2),
                    **metadata,
                },
            )
            metrics.increment("pipeline.stage.success", stage=name)
            metrics.observe_ms("pipeline.stage.duration", duration_ms, stage=name)
            return result
        except Exception as exc:
            duration_ms = (perf_counter() - start_time) * 1000
            trace.stages.append(
                stage_trace.model_copy(
                    update={
                        "finished_at": datetime.now(UTC),
                        "duration_ms": duration_ms,
                        "status": "failed",
                        "error": str(exc),
                    }
                )
            )
            logger.exception(
                "pipeline.stage.failed",
                extra={
                    "request_id": trace.request_id,
                    "stage": name,
                    "duration_ms": round(duration_ms, 2),
                    **metadata,
                },
            )
            metrics.increment("pipeline.stage.failure", stage=name)
            metrics.observe_ms("pipeline.stage.duration", duration_ms, stage=name)
            raise
