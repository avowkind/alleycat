"""OpenAI LLM provider implementation.

This module contains the implementation of the OpenAI LLM provider.

It uses the `openai.AsyncOpenAI` to create the client and the `openai.types.responses`
to define the types for the OpenAI API.

Author: Andrew Watkins <andrew@groat.nz>
"""

from collections.abc import AsyncIterator
from typing import Any, TypedDict, cast

from openai import AsyncOpenAI
from openai.types.responses import Response as OpenAIResponse
from openai.types.responses.response_includable import ResponseIncludable
from openai.types.responses.response_input_param import ResponseInputParam
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.responses.tool_param import ToolParam
from pydantic import BaseModel, Field

from .. import logging
from .base import LLMProvider, Message
from .remote_file import RemoteFile, create_remote_file
from .types import LLMResponse, ResponseFormat, ResponseUsage


class MessageInput(TypedDict):
    """Type for message input."""

    role: str
    content: str
    type: str


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
        self.previous_response_id: str | None = None
        self.remote_file: RemoteFile | None = None

        logging.info(
            f"Initialized OpenAI provider with model=[cyan]{config.model}[/cyan] "
            f"temperature=[cyan]{self.config.temperature}[/cyan]"
        )

    async def close(self) -> None:
        """Clean up resources and close any open connections.

        The provider will not be usable after this
        """
        try:
            # Clean up any file resources first
            if self.remote_file:
                await self.cleanup_file()

            # Close the client if it has a close method
            if hasattr(self.client, "close"):
                await self.client.close()

            self.previous_response_id = None
        except Exception as e:
            logging.error(f"Error during provider cleanup: {e}")
            raise

    def _convert_response(self, response: OpenAIResponse) -> LLMResponse:
        """Convert OpenAI response to our LLMResponse type."""
        usage = None
        if hasattr(response, "usage"):
            usage = ResponseUsage(
                total_tokens=getattr(response.usage, "total_tokens", 0),
                prompt_tokens=getattr(response.usage, "prompt_tokens", 0),
                completion_tokens=getattr(response.usage, "completion_tokens", 0),
            )

        # Store the response ID for continuity in conversations
        if hasattr(response, "id"):
            self.previous_response_id = response.id

        return LLMResponse(
            output_text=response.output_text,
            usage=usage,
        )

    async def add_file(self, file_path: str) -> bool:
        """Add a file for use with the OpenAI API.

        This method creates the appropriate RemoteFile instance based on file type
        and initializes it.

        Args:
            file_path: Path to the file

        Returns:
            True if file setup was successful, False otherwise

        """
        # Clean up any existing file first
        if self.remote_file:
            await self.remote_file.cleanup()

        # Create the appropriate RemoteFile instance
        self.remote_file = create_remote_file(file_path, self.client)

        # Initialize the file (upload or read content)
        return await self.remote_file.initialize()

    async def cleanup_file(self) -> bool:
        """Clean up any file resources.

        Returns:
            True if cleanup was successful, False otherwise

        """
        if self.remote_file:
            result = await self.remote_file.cleanup()
            self.remote_file = None
            return result
        return True

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
        web_search: bool = False,
        vector_store_id: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse | AsyncIterator[ResponseStreamEvent]:
        """Send a request using OpenAI's Responses API."""
        try:
            # Convert string input to proper message format
            message_input: ResponseInputParam
            if isinstance(input, str):
                message_input = cast(ResponseInputParam, MessageInput(role="user", content=input, type="message"))
            else:
                message_input = input

            # Prepare parameters
            params: dict[str, Any] = {
                "model": self.config.model,
                "input": [message_input],  # Input must be a list
                "temperature": self.config.temperature,
            }

            # Add optional parameters if specified
            if max_output_tokens is not None or self.config.max_tokens is not None:
                params["max_output_tokens"] = max_output_tokens or self.config.max_tokens

            if instructions is not None or self.config.instructions is not None:
                params["instructions"] = instructions or self.config.instructions

            if include is not None or self.config.include is not None:
                params["include"] = include or self.config.include

            # Handle tools configuration
            applied_tools: list[ToolParam] = []

            # Add web search tool if enabled
            if web_search:
                applied_tools.append({"type": "web_search_preview"})

            # Add file search tool if vector store ID is provided and explicitly requested
            file_search_requested = any(
                pattern in str(kwargs.get("tools_requested", "")) for pattern in ["file_search", "file-search"]
            )

            if file_search_requested:
                if not vector_store_id:
                    logging.warning("File search tool requested but no vector store ID provided")
                else:
                    logging.info(f"Adding file search tool with vector store ID: {vector_store_id}")

                    # Check if it has the required format (vs_*)
                    if not vector_store_id.startswith("vs_"):
                        logging.warning(f"Vector store ID {vector_store_id} doesn't match required format vs_*")

                    applied_tools.append({"type": "file_search", "vector_store_ids": [vector_store_id]})

            # Add any additional tools specified in parameters or config
            if tools is not None or self.config.tools is not None:
                extra_tools = tools or self.config.tools
                if extra_tools:
                    applied_tools.extend(extra_tools)

            # Set tools parameter if we have any tools
            if applied_tools:
                params["tools"] = applied_tools
                logging.info(f"Using tools: {applied_tools}")

            # Add file references if we have a remote file
            if self.remote_file and isinstance(input, str):
                file_prompt = self.remote_file.get_file_prompt(input)
                params["input"] = [file_prompt]

                # Add additional note to instructions if they exist
                file_instruction = "see attached files for context."
                if "instructions" in params:
                    params["instructions"] = f"{params['instructions']}\n\n{file_instruction}"
                else:
                    params["instructions"] = file_instruction

            # Add conversation continuity if we have a previous response ID
            # Only apply if not explicitly overridden by kwargs
            if self.previous_response_id and "previous_response_id" not in kwargs:
                params["previous_response_id"] = self.previous_response_id

            # Add any other parameters
            params.update(kwargs)

            # Remove any internal parameters that shouldn't be sent to the API
            params.pop("tools_requested", None)

            # Set stream parameter
            if stream:
                params["stream"] = True

            logging.info(f"Sending request to OpenAI: {params}")

            # Call the OpenAI API
            if stream:
                stream_response = await self.client.responses.create(**params)
                # For streaming, wrap the stream in our own to capture the response ID
                return self._wrap_stream_with_id_capture(stream_response)
            else:
                response = await self.client.responses.create(**params)
                return self._convert_response(response)

        except Exception as e:
            logging.error(f"Error during OpenAI request: {str(e)}")
            raise

    async def _wrap_stream_with_id_capture(
        self, stream: AsyncIterator[ResponseStreamEvent]
    ) -> AsyncIterator[ResponseStreamEvent]:
        """Wrap a stream to capture the response ID from completed events."""
        async for event in stream:
            # Capture response ID from completed events
            if event.type == "response.completed" and hasattr(event, "response"):
                self.previous_response_id = event.response.id

            # Always yield the event to the caller
            yield event

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
        provider = OpenAIProvider(config)

        return provider
