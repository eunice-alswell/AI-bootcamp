import asyncio
import logging
from functools import lru_cache

from app.ai.exceptions import AIConfigurationError, AIProviderError, AIRetryableProviderError
from app.ai.models import default_model_config
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.groq import GroqProvider
from app.ai.types import AIRequest, AIResponse, ModelConfig, ProviderName
from app.core.config import Settings, get_settings
from app.observability.telemetry import ai_telemetry

logger = logging.getLogger(__name__)


class AIClientManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._providers: dict[ProviderName, BaseAIProvider] = {}
        self._register_providers()

    async def generate(
        self,
        request: AIRequest,
        model_config: ModelConfig | None = None,
    ) -> AIResponse:
        resolved_config = model_config or request.config or default_model_config(self._settings)
        if request.metadata.get("response_format") == "json_object":
            resolved_config = resolved_config.model_copy(update={"response_format": "json_object"})
        resolved_request = request.model_copy(update={"config": resolved_config})
        try:
            provider = self._get_provider(resolved_config.provider)
        except AIConfigurationError as exc:
            ai_telemetry.record_failure(config=resolved_config, error=exc, attempts=0)
            raise

        last_error: Exception | None = None
        for attempt in range(self._settings.ai_max_retries + 1):
            start_time = ai_telemetry.start_timer()
            try:
                response = await asyncio.wait_for(
                    provider.generate(resolved_request),
                    timeout=resolved_config.timeout_seconds,
                )
                normalized_response = response.model_copy(
                    update={"metadata": {**request.metadata, **response.metadata}}
                )
                ai_telemetry.record_success(
                    start_time=start_time,
                    config=resolved_config,
                    response=normalized_response,
                    attempt=attempt + 1,
                )
                return normalized_response
            except AIRetryableProviderError as exc:
                last_error = exc
                if attempt >= self._settings.ai_max_retries:
                    break
                delay = self._settings.ai_retry_backoff_seconds * (2**attempt)
                ai_telemetry.record_retry(
                    config=resolved_config,
                    attempt=attempt + 1,
                    error=exc,
                    delay=delay,
                )
                logger.warning(
                    "AI provider request failed; retrying",
                    extra={
                        "provider": resolved_config.provider,
                        "model": resolved_config.model,
                        "attempt": attempt + 1,
                        "delay": delay,
                    },
                )
                await asyncio.sleep(delay)
            except asyncio.TimeoutError as exc:
                last_error = exc
                if attempt >= self._settings.ai_max_retries:
                    break
                delay = self._settings.ai_retry_backoff_seconds * (2**attempt)
                ai_telemetry.record_retry(
                    config=resolved_config,
                    attempt=attempt + 1,
                    error=exc,
                    delay=delay,
                )
                logger.warning(
                    "AI provider request timed out; retrying",
                    extra={
                        "provider": resolved_config.provider,
                        "model": resolved_config.model,
                        "attempt": attempt + 1,
                        "delay": delay,
                    },
                )
                await asyncio.sleep(delay)
            except AIProviderError:
                raise

        if last_error is not None:
            ai_telemetry.record_failure(
                config=resolved_config,
                error=last_error,
                attempts=self._settings.ai_max_retries + 1,
            )
        raise AIProviderError("AI provider request failed after retries.") from last_error

    def _register_providers(self) -> None:
        if self._settings.groq_api_key is not None:
            self._providers["groq"] = GroqProvider(
                api_key=self._settings.groq_api_key.get_secret_value(),
                default_timeout_seconds=self._settings.ai_request_timeout_seconds,
            )

    def _get_provider(self, provider_name: ProviderName) -> BaseAIProvider:
        provider = self._providers.get(provider_name)
        if provider is None:
            raise AIConfigurationError(
                f"AI provider '{provider_name}' is not configured. "
                "Check provider API keys and environment settings."
            )
        return provider


@lru_cache
def get_ai_client_manager() -> AIClientManager:
    return AIClientManager(get_settings())
