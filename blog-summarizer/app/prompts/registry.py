from functools import lru_cache

from app.prompts.exceptions import PromptNotFoundError
from app.prompts.loader import PromptTemplateLoader
from app.prompts.renderer import render_prompt
from app.prompts.types import PromptDefinition, RenderedPrompt


class PromptRegistry:
    def __init__(self, loader: PromptTemplateLoader | None = None) -> None:
        self._loader = loader or PromptTemplateLoader()
        self._prompts: dict[str, dict[str, PromptDefinition]] = {}
        self.reload()

    def reload(self) -> None:
        prompts: dict[str, dict[str, PromptDefinition]] = {}
        for prompt in self._loader.load_all():
            prompts.setdefault(prompt.task, {})[prompt.version] = prompt
        self._prompts = prompts

    def list_tasks(self) -> list[str]:
        return sorted(self._prompts)

    def list_versions(self, task: str) -> list[str]:
        return sorted(self._prompts.get(task, {}))

    def get(self, task: str, version: str | None = None) -> PromptDefinition:
        task_versions = self._prompts.get(task)
        if not task_versions:
            raise PromptNotFoundError(f"Prompt task '{task}' was not found.")

        resolved_version = version or self._latest_version(task_versions)
        prompt = task_versions.get(resolved_version)
        if prompt is None:
            fallback_prompt = self._fallback_prompt(task_versions, resolved_version)
            if fallback_prompt is not None:
                return fallback_prompt
            raise PromptNotFoundError(
                f"Prompt task '{task}' version '{resolved_version}' was not found."
            )
        return prompt

    def render(
        self,
        task: str,
        variables: dict,
        version: str | None = None,
    ) -> RenderedPrompt:
        return render_prompt(self.get(task=task, version=version), variables)

    def _latest_version(self, task_versions: dict[str, PromptDefinition]) -> str:
        return sorted(task_versions)[-1]

    def _fallback_prompt(
        self,
        task_versions: dict[str, PromptDefinition],
        requested_version: str,
    ) -> PromptDefinition | None:
        for prompt in task_versions.values():
            if prompt.version == requested_version and prompt.fallback_version:
                return task_versions.get(prompt.fallback_version)
        fallback_versions = [
            prompt.fallback_version for prompt in task_versions.values() if prompt.fallback_version
        ]
        for fallback_version in fallback_versions:
            fallback_prompt = task_versions.get(fallback_version)
            if fallback_prompt is not None:
                return fallback_prompt
        return None


@lru_cache
def get_prompt_registry() -> PromptRegistry:
    return PromptRegistry()
