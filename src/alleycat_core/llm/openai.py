"""OpenAI LLM provider implementation."""

from collections.abc import AsyncIterator
from typing import Any

from openai import AsyncOpenAI
from openai.types.responses import Response as OpenAIResponse
from openai.types.responses.response_includable import ResponseIncludable
from openai.types.responses.response_input_param import ResponseInputParam
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from openai.types.responses.tool_param import ToolParam
from pydantic import BaseModel, Field

from .. import logging
from .base import LLMProvider, Message


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI provider."""

    api_key: str
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    response_format: dict[str, str] | None = None
    instructions: str | None = None  # System message for responses API
    tools: list[ToolParam] | None = None  # Tools for function calling
    include: list[ResponseIncludable] | None = None  # Additional data to include in response


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider."""

    def __init__(self, config: OpenAIConfig):
        """Initialize the OpenAI provider."""
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key)
        logging.info(
            f"Initialized OpenAI provider with model=[cyan]{config.model}[/cyan] "
            f"temperature=[cyan]{self.config.temperature}[/cyan]"
        )

    async def respond(
        self,
        input: str | ResponseInputParam,
        *,
        stream: bool = False,
        include: list[ResponseIncludable] | None = None,
        instructions: str | None = None,
        max_output_tokens: int | None = None,
        tools: list[ToolParam] | None = None,
        text: ResponseTextConfigParam | None = None,
        **kwargs: Any,
    ) -> OpenAIResponse | AsyncIterator[ResponseStreamEvent]:
        """Send a request using OpenAI's Responses API."""
        try:
            params = {
                "model": self.config.model,
                "input": input,
                "temperature": self.config.temperature,
                "max_output_tokens": max_output_tokens or self.config.max_tokens,
            }

            if instructions or self.config.instructions:
                params["instructions"] = instructions or self.config.instructions
            if include or self.config.include:
                params["include"] = include or self.config.include
            if tools or self.config.tools:
                params["tools"] = tools or self.config.tools
            if text or self.config.response_format:
                # TODO: this is not how the text field works
                params["text"] = text or {"format": "json"} if self.config.response_format else None

            params.update(kwargs)

            if stream:
                return await self.client.responses.create(**params, stream=True)
            else:
                return await self.client.responses.create(**params)

        except Exception as e:
            logging.error(f"Error during OpenAI request: {str(e)}")
            raise

    async def complete(self, messages: list[Message], **kwargs) -> OpenAIResponse:
        """Send a completion request using responses API."""
        input_text = messages[-1].content if messages else ""
        instructions = messages[0].content if len(messages) > 1 else None
        return await self.respond(input=input_text, instructions=instructions, **kwargs)

    async def complete_stream(
        self, messages: list[Message], **kwargs
    ) -> AsyncIterator[ResponseStreamEvent]:
        """Stream a completion request using responses API."""
        input_text = messages[-1].content if messages else ""
        instructions = messages[0].content if len(messages) > 1 else None
        return await self.respond(input=input_text,
                                  instructions=instructions,
                                  stream=True, **kwargs)


class OpenAIFactory:
    """Factory for creating OpenAI providers."""

    def create(self, **kwargs) -> LLMProvider:
        """Create an OpenAI provider instance."""
        logging.info("Creating OpenAI provider with configuration:", style="bold")
        for key, value in kwargs.items():
            if key != "api_key":  # Don't log sensitive information
                logging.info(f"  {key}: [cyan]{value}[/cyan]")

        # Handle output format configuration
        if kwargs.get("output_format") == "json":
            kwargs["response_format"] = {"type": "json"}
            # Remove output_format as it's not part of OpenAIConfig
            kwargs.pop("output_format", None)

        config = OpenAIConfig(**kwargs)
        return OpenAIProvider(config)
