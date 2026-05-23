from pathlib import Path
import tomllib
from app.prompts.exceptions import PromptValidationError
from app.prompts.renderer import get_template_variables
from app.prompts.types import PromptDefinition


class PromptTemplateLoader:
    def __init__(self, root_path: Path | None = None) -> None:
        self._root_path = root_path or Path(__file__).parent / "templates"

    def load_all(self) -> list[PromptDefinition]:
        definitions: list[PromptDefinition] = []
        for path in sorted(self._root_path.rglob("*.toml")):
            definitions.append(self.load_file(path))
        return definitions

    def load_file(self, path: Path) -> PromptDefinition:
        with path.open("rb") as template_file:
            raw_data = tomllib.load(template_file)

        prompt = PromptDefinition.model_validate(raw_data)
        self._validate_template_variables(prompt, path)
        return prompt

    def _validate_template_variables(self, prompt: PromptDefinition, path: Path) -> None:
        known_variables = set(prompt.required_variables) | set(prompt.optional_variables)
        referenced_variables: set[str] = set()

        for message in prompt.messages:
            referenced_variables.update(get_template_variables(message.template))

        unknown_variables = referenced_variables - known_variables
        if unknown_variables:
            raise PromptValidationError(
                f"Prompt file '{path}' references undeclared variables: "
                f"{', '.join(sorted(unknown_variables))}"
            )

        unused_required_variables = set(prompt.required_variables) - referenced_variables
        if unused_required_variables:
            raise PromptValidationError(
                f"Prompt file '{path}' declares unused required variables: "
                f"{', '.join(sorted(unused_required_variables))}"
            )
