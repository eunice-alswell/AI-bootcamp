from typing import Any, Literal

from pydantic import BaseModel, Field

MessageRole = Literal["system", "user", "assistant", "tool"]
ProviderName = Literal["groq", "openai", "claude", "gemini"]
ResponseFormat = Literal["text", "json_object"]


class AIMessage(BaseModel):
    role: MessageRole
    content: str


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ModelConfig(BaseModel):
    provider: ProviderName
    model: str
    temperature: float = 0.2
    max_tokens: int = 1024
    timeout_seconds: float = 30.0
    response_format: ResponseFormat = "text"


class AIRequest(BaseModel):
    messages: list[AIMessage]
    config: ModelConfig | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    provider: ProviderName
    model: str
    content: str
    usage: TokenUsage
    finish_reason: str | None = None
    raw_response_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
