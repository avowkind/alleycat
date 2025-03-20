"""OpenAI LLM provider implementation.

This module contains the implementation of the OpenAI LLM provider.

It uses the `openai.AsyncOpenAI` to create the client and the `openai.types.responses`
to define the types for the OpenAI API.

Author: Andrew Watkins <andrew@groat.nz>
"""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

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
    file_path: str | None = None  # Path to a file to upload
    file_id: str | None = None  # ID of the uploaded file


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider."""

    def __init__(self, config: OpenAIConfig):
        """Initialize the OpenAI provider."""
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key)
        self.previous_response_id: str | None = None
        self.file_id: str | None = config.file_id
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

        # Store the response ID for continuity in conversations
        if hasattr(response, "id"):
            self.previous_response_id = response.id

        return LLMResponse(
            output_text=response.output_text,
            usage=usage,
        )

    async def upload_file(self, file_path: str) -> str:
        """Upload a file to OpenAI.

        Args:
            file_path: Path to the file to upload

        Returns:
            The file ID

        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check file extension - OpenAI currently only supports certain file types
        supported_extensions = [".pdf", ".json", ".jsonl", ".txt", ".csv", ".md"]
        if path.suffix.lower() not in supported_extensions:
            raise ValueError(
                f"Unsupported file format: {path.suffix}. "
                f"Currently supported formats: {', '.join(supported_extensions)}"
            )

        try:
            with open(path, "rb") as file:
                response = await self.client.files.create(
                    file=file,
                    purpose="assistants",
                )

            self.file_id = response.id
            logging.info(f"Uploaded file [cyan]{path.name}[/cyan] with ID [cyan]{self.file_id}[/cyan]")
            return self.file_id
        except Exception as e:
            error_msg = str(e)
            # Check for common error cases and provide more helpful messages
            if "context_length_exceeded" in error_msg or "maximum limit" in error_msg:
                logging.error("File too large: The file exceeds the maximum token limit for the chosen model.")
                logging.error("Try using a smaller file or splitting the content into multiple smaller files.")
            elif "invalid_request_error" in error_msg and "file type" in error_msg:
                logging.error(f"Invalid file format: {error_msg}")
                logging.error(f"Supported formats: {', '.join(supported_extensions)}")
            else:
                logging.error(f"Error uploading file: {error_msg}")
            raise

    async def delete_file(self, file_id: str | None = None) -> bool:
        """Delete a file from OpenAI.

        Args:
            file_id: ID of the file to delete. If None, uses the stored file_id.

        Returns:
            True if the file was deleted, False otherwise

        """
        target_id = file_id or self.file_id
        if not target_id:
            logging.warning("No file ID provided for deletion")
            return False

        try:
            await self.client.files.delete(target_id)
            logging.info(f"Deleted file with ID [cyan]{target_id}[/cyan]")
            if target_id == self.file_id:
                self.file_id = None
            return True
        except Exception as e:
            logging.error(f"Error deleting file: {str(e)}")
            return False

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

            # Add file references if we have a file ID
            if self.file_id:
                # Format the input as a structured object with the file reference
                if isinstance(input, str):
                    # Create a special message that includes the file reference
                    # This preserves any instructions that might have been set above
                    structured_input = {
                        "role": "user",
                        "content": [
                            {"type": "input_file", "file_id": self.file_id},
                            {"type": "input_text", "text": input},
                        ],
                    }
                    # OpenAI expects an array of input items, not a single object
                    params["input"] = [structured_input]
                    logging.info(f"Including file ID [cyan]{self.file_id}[/cyan] in structured input")

                    # Add additional note to instructions if they exist
                    file_instruction = "The user has attached a file for you to analyze."
                    if "instructions" in params:
                        params["instructions"] = f"{params['instructions']}\n\n{file_instruction}"
                    else:
                        params["instructions"] = file_instruction
                else:
                    # Input is already structured, log a warning
                    logging.warning("File ID available but input is already structured. File might not be included.")

            # Convert our ResponseFormat to OpenAI's expected format
            if text is not None or self.config.response_format is not None:
                format_config = text or self.config.response_format
                if format_config is not None and "format" in format_config:
                    format_value = format_config["format"]
                    if format_value in ["text", "markdown", "json"]:
                        params["text"] = {"format": format_value}

            # Add conversation continuity if we have a previous response ID
            # Only apply if not explicitly overridden by kwargs
            if self.previous_response_id and "previous_response_id" not in kwargs:
                params["previous_response_id"] = self.previous_response_id

            # Add any other parameters
            params.update(kwargs)

            # Set stream parameter
            if stream:
                params["stream"] = True

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

        # If file path is provided but file_id is not, upload the file
        if kwargs.get("file_path") and not kwargs.get("file_id"):
            logging.warning("File path provided without file_id, but upload should be handled by CLI")

        config = OpenAIConfig(**kwargs)
        return OpenAIProvider(config)
