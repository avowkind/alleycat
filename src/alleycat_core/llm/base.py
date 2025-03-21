"""Base classes and types for LLM providers.

This module defines the core interfaces and types for interacting with different
LLM providers. It includes base classes for chat messages and responses, as well
as a factory protocol for creating LLM provider instances.

Author: Andrew Watkins <andrew@groat.nz>
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Protocol

from openai.types.responses.response_includable import ResponseIncludable
from openai.types.responses.response_input_param import ResponseInputParam
from openai.types.responses.response_stream_event import ResponseStreamEvent
from openai.types.responses.tool_param import ToolParam
from pydantic import BaseModel

from .types import LLMResponse, ResponseFormat


class Message(BaseModel):
    """A chat message."""

    role: str
    content: str


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
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
        """Send a request to the LLM.

        Args:
            input: The input text or structured input parameter
            stream: Whether to stream the response
            include: Additional data to include in response
            instructions: System message for responses API
            max_output_tokens: Maximum number of tokens to generate
            tools: Tools for function calling
            text: Text format configuration
            web_search: Enable web search functionality
            vector_store_id: Vector store ID for file search
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse or AsyncIterator[ResponseStreamEvent] containing the LLM's response

        """
        pass

    @abstractmethod
    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        """Send a completion request to the LLM.

        Args:
            messages: List of messages in the conversation
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse containing the LLM's response

        """
        pass

    @abstractmethod
    async def complete_stream(self, messages: list[Message], **kwargs: Any) -> AsyncIterator[ResponseStreamEvent]:
        """Stream a completion request from the LLM.

        Args:
            messages: List of messages in the conversation
            **kwargs: Additional provider-specific parameters

        Yields:
            ResponseStreamEvent chunks as they arrive from the LLM

        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources and close any open connections.

        This method should be called when the provider is no longer needed.
        It should clean up any resources, close connections, and handle any necessary cleanup.
        """
        pass

    @abstractmethod
    async def add_file(self, file_path: str) -> bool:
        """Add a file for use with the LLM.

        Args:
            file_path: Path to the file to add

        Returns:
            True if file was added successfully, False otherwise

        """
        pass


class LLMFactory(Protocol):
    """Protocol for LLM provider factories."""

    def create(self, **kwargs: Any) -> LLMProvider:
        """Create an LLM provider instance.

        Args:
            **kwargs: Provider-specific configuration

        Returns:
            An instance of an LLM provider

        """
        pass
