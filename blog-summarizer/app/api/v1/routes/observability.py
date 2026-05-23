from fastapi import APIRouter

from app.observability.metrics import metrics

router = APIRouter(prefix="/observability")


@router.get("/metrics")
async def get_metrics() -> dict:
    return metrics.snapshot()
