from app.core.config import Settings
from app.ai.types import ModelConfig, ProviderName


SUPPORTED_PROVIDERS: set[ProviderName] = {"groq", "openai", "claude", "gemini"}

DEFAULT_MODELS: dict[ProviderName, str] = {
    "groq": "llama-3.1-8b-instant",
    "openai": "gpt-4.1-mini",
    "claude": "claude-sonnet-4-5",
    "gemini": "gemini-2.5-flash",
}


def default_model_config(settings: Settings) -> ModelConfig:
    return ModelConfig(
        provider=settings.ai_default_provider,
        model=settings.ai_default_model or DEFAULT_MODELS[settings.ai_default_provider],
        temperature=settings.ai_default_temperature,
        max_tokens=settings.ai_default_max_tokens,
        timeout_seconds=settings.ai_request_timeout_seconds,
    )
