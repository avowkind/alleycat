"""OpenAI LLM provider implementation."""

from typing import AsyncIterator

from openai import AsyncOpenAI
from pydantic import BaseModel

from .. import logging
from .base import ChatResponse, LLMProvider, Message


class OpenAIConfig(BaseModel):
    """Configuration for OpenAI provider."""
    
    api_key: str
    model: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int | None = None


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider."""
    
    def __init__(self, config: OpenAIConfig):
        """Initialize the OpenAI provider.
        
        Args:
            config: OpenAI configuration
        """
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key)
        logging.info(
            f"Initialized OpenAI provider with model=[cyan]{config.model}[/cyan] "
            f"temperature=[cyan]{config.temperature}[/cyan]"
        )
        
    async def complete(self, messages: list[Message], **kwargs) -> ChatResponse:
        """Send a completion request to OpenAI.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Returns:
            ChatResponse containing OpenAI's response
        """
        logging.debug(
            f"Sending completion request to OpenAI:\n"
            f"  Model: [cyan]{self.config.model}[/cyan]\n"
            f"  Messages: [cyan]{len(messages)}[/cyan]\n"
            f"  Temperature: [cyan]{self.config.temperature}[/cyan]"
        )
        
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=False,
            **kwargs
        )
        
        choice = response.choices[0]
        usage = dict(response.usage)
        
        # Debug log the raw usage data
        logging.debug(f"Raw usage data: {usage}")
        
        # Filter out any non-integer values from usage
        usage = {k: v for k, v in usage.items() if isinstance(v, int)}
        
        logging.debug(
            f"Received response from OpenAI:\n"
            f"  Tokens used: [cyan]{usage.get('total_tokens', 'unknown')}[/cyan]\n"
            f"  Finish reason: [cyan]{choice.finish_reason}[/cyan]"
        )
        
        return ChatResponse(
            content=choice.message.content,
            finish_reason=choice.finish_reason,
            usage=usage
        )
        
    async def complete_stream(
        self, messages: list[Message], **kwargs
    ) -> AsyncIterator[ChatResponse]:
        """Stream a completion request from OpenAI.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional parameters to pass to the OpenAI API
            
        Yields:
            ChatResponse chunks as they arrive from OpenAI
        """
        logging.debug(
            f"Starting streaming completion request to OpenAI:\n"
            f"  Model: [cyan]{self.config.model}[/cyan]\n"
            f"  Messages: [cyan]{len(messages)}[/cyan]\n"
            f"  Temperature: [cyan]{self.config.temperature}[/cyan]"
        )
        
        stream = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield ChatResponse(
                    content=chunk.choices[0].delta.content,
                    finish_reason=chunk.choices[0].finish_reason
                )


class OpenAIFactory:
    """Factory for creating OpenAI providers."""
    
    def create(self, **kwargs) -> LLMProvider:
        """Create an OpenAI provider instance.
        
        Args:
            **kwargs: OpenAI configuration parameters
            
        Returns:
            An instance of OpenAIProvider
        """
        logging.info("Creating OpenAI provider with configuration:", style="bold")
        for key, value in kwargs.items():
            if key != "api_key":  # Don't log sensitive information
                logging.info(f"  {key}: [cyan]{value}[/cyan]")
                
        config = OpenAIConfig(**kwargs)
        return OpenAIProvider(config) 