from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.ai.types import AIMessage, AIRequest, ModelConfig

PromptRole = Literal["system", "user", "assistant"]


class PromptMessageTemplate(BaseModel):
    role: PromptRole
    template: str


class PromptOutputSpec(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    response_format: Literal["text", "json_object"] = "text"
    schema_name: str | None = None
    json_schema: dict[str, Any] | None = Field(default=None, alias="schema")


class PromptExample(BaseModel):
    name: str
    audience: str
    variables: dict[str, Any]


class PromptDefinition(BaseModel):
    task: str
    version: str
    description: str
    required_variables: list[str] = Field(default_factory=list)
    optional_variables: dict[str, Any] = Field(default_factory=dict)
    fallback_version: str | None = None
    output: PromptOutputSpec = Field(default_factory=PromptOutputSpec)
    messages: list[PromptMessageTemplate]
    examples: list[PromptExample] = Field(default_factory=list)


class RenderedPrompt(BaseModel):
    task: str
    version: str
    messages: list[AIMessage]
    output: PromptOutputSpec
    variables: dict[str, Any]

    def to_ai_request(self, config: ModelConfig | None = None) -> AIRequest:
        if config is not None and self.output.response_format == "json_object":
            config = config.model_copy(update={"response_format": "json_object"})

        return AIRequest(
            messages=self.messages,
            config=config,
            metadata={
                "prompt_task": self.task,
                "prompt_version": self.version,
                "response_format": self.output.response_format,
            },
        )


class PromptTestCase(BaseModel):
    name: str
    task: str
    variables: dict[str, Any]
    version: str | None = None
    expected_required_phrases: list[str] = Field(default_factory=list)
