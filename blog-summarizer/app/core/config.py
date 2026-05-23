from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )

    app_name: str = "Blog Summarizer API"
    app_version: str = "0.1.0"
    environment: Literal["local", "development", "staging", "production"] = "local"
    debug: bool = True

    host: str = "127.0.0.1"
    port: int = 8000
    api_v1_prefix: str = "/api/v1"

    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=list)
    allowed_hosts: list[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost"])

    ai_default_provider: Literal["groq", "openai", "claude", "gemini"] = "groq"
    ai_default_model: str = "llama-3.1-8b-instant"
    ai_request_timeout_seconds: float = 30.0
    ai_max_retries: int = 2
    ai_retry_backoff_seconds: float = 0.5
    ai_default_temperature: float = 0.2
    ai_default_max_tokens: int = 1024

    groq_api_key: SecretStr | None = None

    pipeline_chunk_target_tokens: int = 1200
    pipeline_chunk_overlap_tokens: int = 120
    pipeline_max_article_tokens: int = 6000
    pipeline_allow_extractive_fallback: bool = True

    security_max_request_bytes: int = 1_000_000
    security_rate_limit_requests: int = 60
    security_rate_limit_window_seconds: int = 60
    security_block_high_risk_input: bool = True
    security_block_high_risk_output: bool = False
    security_prompt_injection_threshold: float = 0.65
    security_malicious_input_threshold: float = 0.75

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def parse_csv_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("groq_api_key", mode="before")
    @classmethod
    def empty_secret_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
