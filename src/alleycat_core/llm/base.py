"""Base interfaces for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Protocol

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A chat message."""
    
    role: str
    content: str


class ChatResponse(BaseModel):
    """A response from the LLM."""
    
    content: str
    finish_reason: str | None = None
    usage: dict[str, Any] | None = Field(
        default=None,
        description="Usage statistics from the LLM. Keys and value types may vary by provider."
    )


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def complete(self, messages: list[Message], **kwargs) -> ChatResponse:
        """Send a completion request to the LLM.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional provider-specific parameters
            
        Returns:
            ChatResponse containing the LLM's response
        """
        pass

    @abstractmethod
    async def complete_stream(
        self, messages: list[Message], **kwargs
    ) -> AsyncIterator[ChatResponse]:
        """Stream a completion request from the LLM.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional provider-specific parameters
            
        Yields:
            ChatResponse chunks as they arrive from the LLM
        """
        pass


class LLMFactory(Protocol):
    """Protocol for LLM provider factories."""
    
    def create(self, **kwargs) -> LLMProvider:
        """Create an LLM provider instance.
        
        Args:
            **kwargs: Provider-specific configuration
            
        Returns:
            An instance of an LLM provider
        """
        pass 