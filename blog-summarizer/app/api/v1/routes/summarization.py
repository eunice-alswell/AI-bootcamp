from fastapi import APIRouter

from app.pipeline.orchestrator import BlogSummarizationPipeline
from app.pipeline.types import BlogSummarizationPipelineResult
from app.observability.correlation import get_request_id
from app.schemas.summarization import SummarizationRequest

router = APIRouter(prefix="/summaries")


@router.post("", response_model=BlogSummarizationPipelineResult)
async def summarize_blog(request: SummarizationRequest) -> BlogSummarizationPipelineResult:
    request_id = get_request_id()
    if request_id:
        request = request.model_copy(
            update={"metadata": request.metadata.model_copy(update={"request_id": request_id})}
        )
    return await BlogSummarizationPipeline().run(request)
