from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.schemas.common import RequestMetadata, ResponseMetadata

ConfidenceLevel = Literal["low", "medium", "high"]


class SummarizationRequest(BaseModel):
    article_text: str = Field(min_length=50)
    source_url: HttpUrl | None = None
    audience: str = "general readers"
    tone: str = "clear, concise, and neutral"
    summary_length: Literal["short", "medium", "long"] = "medium"
    focus_area: str = "the article's most useful ideas"
    metadata: RequestMetadata = Field(default_factory=RequestMetadata)


class BlogSummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=160)
    summary: str = Field(min_length=20)
    key_points: list[str] = Field(min_length=3, max_length=7)
    audience_takeaway: str = Field(min_length=10)
    confidence: ConfidenceLevel

    @field_validator("key_points")
    @classmethod
    def validate_key_points(cls, value: list[str]) -> list[str]:
        if any(not point.strip() for point in value):
            raise ValueError("key_points cannot contain empty items")
        return value


class SummarizationResponse(BaseModel):
    data: BlogSummaryOutput
    metadata: ResponseMetadata
