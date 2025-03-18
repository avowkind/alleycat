"""OpenAI LLM provider implementation.

This module contains the implementation of the OpenAI LLM provider.

It uses the `openai.AsyncOpenAI` to create the client and the `openai.types.responses`
to define the types for the OpenAI API.

Author: Andrew Watkins <andrew@groat.nz>
"""

from collections.abc import AsyncIterator
from typing import Any, cast

from openai import AsyncOpenAI
from openai.types.responses import Response as OpenAIResponse
from openai.types.responses.response_includable import ResponseIncludable
from openai.types.responses.response_input_param import ResponseInputParam
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.responses.tool_param import ToolParam
from pydantic import BaseModel, Field

from .. import logging
from .base import LLMProvider, Message
from .types import LLMResponse, ResponseFormat, ResponseUsage


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI provider."""

    api_key: str
    model: str = "gpt-4o-mini"
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int | None = None
    response_format: ResponseFormat = None
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

    def _convert_response(self, response: OpenAIResponse) -> LLMResponse:
        """Convert OpenAI response to our LLMResponse type."""
        usage = None
        if hasattr(response, "usage"):
            usage = ResponseUsage(
                total_tokens=getattr(response.usage, "total_tokens", 0),
                prompt_tokens=getattr(response.usage, "prompt_tokens", 0),
                completion_tokens=getattr(response.usage, "completion_tokens", 0),
            )

        return LLMResponse(
            output_text=response.output_text,
            usage=usage,
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
        text: ResponseFormat = None,
        **kwargs: Any,
    ) -> LLMResponse | AsyncIterator[ResponseStreamEvent]:
        """Send a request using OpenAI's Responses API."""
        try:
            # Prepare parameters
            params: dict[str, Any] = {
                "model": self.config.model,
                "input": input,
                "temperature": self.config.temperature,
            }

            # Add optional parameters if specified
            if max_output_tokens is not None or self.config.max_tokens is not None:
                params["max_output_tokens"] = max_output_tokens or self.config.max_tokens

            if instructions is not None or self.config.instructions is not None:
                params["instructions"] = instructions or self.config.instructions

            if include is not None or self.config.include is not None:
                params["include"] = include or self.config.include

            if tools is not None or self.config.tools is not None:
                params["tools"] = tools or self.config.tools

            # Convert our ResponseFormat to OpenAI's expected format
            if text is not None or self.config.response_format is not None:
                format_config = text or self.config.response_format
                if format_config is not None and "format" in format_config:
                    format_value = format_config["format"]
                    if format_value in ["text", "markdown", "json"]:
                        params["text"] = {"format": format_value}

            # Add any other parameters
            params.update(kwargs)

            # Set stream parameter
            if stream:
                params["stream"] = True

            # Call the OpenAI API
            if stream:
                stream_response = await self.client.responses.create(**params)
                return cast(AsyncIterator[ResponseStreamEvent], stream_response)
            else:
                response = await self.client.responses.create(**params)
                return self._convert_response(response)

        except Exception as e:
            logging.error(f"Error during OpenAI request: {str(e)}")
            raise

    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        """Send a completion request using responses API."""
        input_text = messages[-1].content if messages else ""
        instructions = messages[0].content if len(messages) > 1 else None
        response = await self.respond(input=input_text, instructions=instructions, **kwargs)
        if isinstance(response, AsyncIterator):
            raise ValueError("Unexpected streaming response in non-streaming call")
        return response

    async def complete_stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[ResponseStreamEvent]:
        """Stream a completion request using responses API."""
        input_text = messages[-1].content if messages else ""
        instructions = messages[0].content if len(messages) > 1 else None
        response = await self.respond(input=input_text, instructions=instructions, stream=True, **kwargs)
        if not isinstance(response, AsyncIterator):
            raise ValueError("Expected streaming response")
        return response


class OpenAIFactory:
    """Factory for creating OpenAI providers."""

    def create(self, **kwargs: Any) -> LLMProvider:
        """Create an OpenAI provider instance."""
        logging.info("Creating OpenAI provider with configuration:", style="bold")
        for key, value in kwargs.items():
            if key != "api_key":  # Don't log sensitive information
                logging.info(f"  {key}: [cyan]{value}[/cyan]")

        # Handle output format configuration
        if kwargs.get("output_format") == "json":
            kwargs["response_format"] = {"format": "json"}
            # Remove output_format as it's not part of OpenAIConfig
            kwargs.pop("output_format", None)

        config = OpenAIConfig(**kwargs)
        return OpenAIProvider(config)
