from app.ai.types import AIRequest, ModelConfig
from app.prompts.registry import PromptRegistry, get_prompt_registry
from app.prompts.types import RenderedPrompt


class PromptBuilder:
    def __init__(self, registry: PromptRegistry | None = None) -> None:
        self._registry = registry or get_prompt_registry()

    def build(
        self,
        task: str,
        variables: dict,
        version: str | None = None,
    ) -> RenderedPrompt:
        return self._registry.render(task=task, version=version, variables=variables)

    def build_ai_request(
        self,
        task: str,
        variables: dict,
        version: str | None = None,
        config: ModelConfig | None = None,
    ) -> AIRequest:
        return self.build(task=task, version=version, variables=variables).to_ai_request(config=config)
