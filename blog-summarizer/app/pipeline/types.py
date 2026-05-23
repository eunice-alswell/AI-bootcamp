from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.ai.types import AIRequest, AIResponse
from app.guardrails.schemas import SafetyAssessment
from app.schemas.summarization import SummarizationRequest, SummarizationResponse
from app.validation.schemas import ValidationReport

PipelineStatus = Literal["success", "degraded", "failed"]


class BlogDocument(BaseModel):
    text: str
    source_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContentChunk(BaseModel):
    index: int
    text: str
    estimated_tokens: int


class TokenEstimate(BaseModel):
    characters: int
    words: int
    estimated_tokens: int


class PipelineStageTrace(BaseModel):
    name: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: float | None = None
    status: Literal["success", "failed"] = "success"
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class PipelineTrace(BaseModel):
    request_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    duration_ms: float | None = None
    stages: list[PipelineStageTrace] = Field(default_factory=list)


class PipelineContext(BaseModel):
    request: SummarizationRequest
    document: BlogDocument | None = None
    cleaned_text: str | None = None
    token_estimate: TokenEstimate | None = None
    chunks: list[ContentChunk] = Field(default_factory=list)
    ai_request: AIRequest | None = None
    ai_response: AIResponse | None = None
    validation_report: ValidationReport | None = None
    response: SummarizationResponse | None = None
    safety: SafetyAssessment = Field(default_factory=SafetyAssessment)
    fallback_used: bool = False


class BlogSummarizationPipelineResult(BaseModel):
    status: PipelineStatus
    response: SummarizationResponse | None
    validation_report: ValidationReport | None
    safety: SafetyAssessment
    trace: PipelineTrace
    fallback_used: bool = False
