from abc import ABC, abstractmethod

from app.ai.types import AIRequest, AIResponse, ProviderName


class BaseAIProvider(ABC):
    provider_name: ProviderName

    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        """Run an async inference request and return a normalized response."""
