from string import Formatter
from typing import Any

from app.ai.types import AIMessage
from app.prompts.exceptions import PromptRenderError
from app.prompts.types import PromptDefinition, RenderedPrompt


def render_prompt(prompt: PromptDefinition, variables: dict[str, Any]) -> RenderedPrompt:
    merged_variables = {**prompt.optional_variables, **variables}
    missing_variables = [
        variable for variable in prompt.required_variables if variable not in merged_variables
    ]
    if missing_variables:
        raise PromptRenderError(
            f"Prompt '{prompt.task}' version '{prompt.version}' is missing variables: "
            f"{', '.join(missing_variables)}"
        )

    messages = [
        AIMessage(
            role=message.role,
            content=_render_template(message.template, merged_variables),
        )
        for message in prompt.messages
    ]

    return RenderedPrompt(
        task=prompt.task,
        version=prompt.version,
        messages=messages,
        output=prompt.output,
        variables=merged_variables,
    )


def get_template_variables(template: str) -> set[str]:
    return {
        field_name
        for _, field_name, _, _ in Formatter().parse(template)
        if field_name is not None and field_name
    }


def _render_template(template: str, variables: dict[str, Any]) -> str:
    try:
        return template.format(**variables)
    except KeyError as exc:
        raise PromptRenderError(f"Missing prompt variable: {exc.args[0]}") from exc
    except ValueError as exc:
        raise PromptRenderError("Prompt template contains invalid format syntax.") from exc
