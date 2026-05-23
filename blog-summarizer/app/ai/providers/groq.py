from typing import Any

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncGroq,
    RateLimitError,
)

from app.ai.exceptions import (
    AIProviderError,
    AIResponseFormatError,
    AIRetryableProviderError,
    AITimeoutError,
)
from app.ai.providers.base import BaseAIProvider
from app.ai.types import AIRequest, AIResponse, TokenUsage


class GroqProvider(BaseAIProvider):
    provider_name = "groq"

    def __init__(self, api_key: str, default_timeout_seconds: float, max_retries: int = 0) -> None:
        self._client = AsyncGroq(
            api_key=api_key,
            timeout=default_timeout_seconds,
            max_retries=max_retries,
        )

    async def generate(self, request: AIRequest) -> AIResponse:
        model_config = request.config
        if model_config is None:
            raise AIProviderError("Groq requests require a resolved model config.")

        try:
            response = await self._client.chat.completions.create(
                model=model_config.model,
                messages=[message.model_dump() for message in request.messages],
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                response_format=self._response_format(model_config.response_format),
                timeout=model_config.timeout_seconds,
            )
        except APITimeoutError as exc:
            raise AITimeoutError("Groq request timed out.") from exc
        except (APIConnectionError, RateLimitError) as exc:
            raise AIRetryableProviderError("Groq request failed with a retryable error.") from exc
        except APIStatusError as exc:
            if exc.status_code >= 500 or exc.status_code == 429:
                raise AIRetryableProviderError("Groq service returned a retryable status.") from exc
            raise AIProviderError(f"Groq service returned status {exc.status_code}.") from exc
        except Exception as exc:
            raise AIProviderError("Groq request failed.") from exc

        return self._normalize_response(response, model_config.model)

    def _response_format(self, response_format: str) -> dict[str, str] | None:
        if response_format == "json_object":
            return {"type": "json_object"}
        return None

    def _normalize_response(self, response: Any, model: str) -> AIResponse:
        try:
            choice = response.choices[0]
            message = choice.message
            usage = response.usage
            return AIResponse(
                provider=self.provider_name,
                model=model,
                content=message.content or "",
                usage=TokenUsage(
                    prompt_tokens=usage.prompt_tokens or 0,
                    completion_tokens=usage.completion_tokens or 0,
                    total_tokens=usage.total_tokens or 0,
                ),
                finish_reason=choice.finish_reason,
                raw_response_id=response.id,
            )
        except (AttributeError, IndexError, TypeError) as exc:
            raise AIResponseFormatError("Groq response could not be normalized.") from exc
