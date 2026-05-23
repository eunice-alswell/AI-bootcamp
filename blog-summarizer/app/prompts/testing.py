from app.prompts.registry import PromptRegistry, get_prompt_registry
from app.prompts.types import PromptTestCase


class PromptTestResult:
    def __init__(self, name: str, passed: bool, failures: list[str]) -> None:
        self.name = name
        self.passed = passed
        self.failures = failures


class PromptTester:
    def __init__(self, registry: PromptRegistry | None = None) -> None:
        self._registry = registry or get_prompt_registry()

    def run(self, test_case: PromptTestCase) -> PromptTestResult:
        rendered = self._registry.render(
            task=test_case.task,
            version=test_case.version,
            variables=test_case.variables,
        )
        rendered_text = "\n".join(message.content for message in rendered.messages)
        failures = [
            phrase
            for phrase in test_case.expected_required_phrases
            if phrase not in rendered_text
        ]
        return PromptTestResult(
            name=test_case.name,
            passed=not failures,
            failures=failures,
        )
