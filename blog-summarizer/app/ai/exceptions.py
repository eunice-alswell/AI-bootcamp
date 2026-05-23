class AIError(Exception):
    """Base exception for AI infrastructure failures."""


class AIConfigurationError(AIError):
    """Raised when an AI provider is not configured correctly."""


class AIProviderError(AIError):
    """Raised when a provider returns a non-retryable failure."""


class AIRetryableProviderError(AIProviderError):
    """Raised when a provider failure can be retried."""


class AITimeoutError(AIRetryableProviderError):
    """Raised when an inference request exceeds its timeout."""


class AIResponseFormatError(AIProviderError):
    """Raised when a provider response cannot be normalized."""
