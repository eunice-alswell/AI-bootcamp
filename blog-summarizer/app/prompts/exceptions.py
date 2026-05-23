class PromptError(Exception):
    """Base exception for prompt management failures."""


class PromptNotFoundError(PromptError):
    """Raised when a prompt task or version cannot be found."""


class PromptRenderError(PromptError):
    """Raised when a prompt cannot be rendered with the provided variables."""


class PromptValidationError(PromptError):
    """Raised when a prompt definition is invalid."""
