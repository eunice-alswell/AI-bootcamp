from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RequestMetadata(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    source: str | None = None
    user_id: str | None = None


class ResponseMetadata(BaseModel):
    request_id: str
    model: str | None = None
    provider: str | None = None
    prompt_task: str | None = None
    prompt_version: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    token_usage: dict[str, int] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)
