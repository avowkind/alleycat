"""Type definitions for LLM responses and events.

This module contains type definitions for LLM responses and events.

It uses the `pydantic.BaseModel` to define the types and the `openai.types.responses`
to define the types for the OpenAI API.

Author: Andrew Watkins <andrew@groat.nz>
"""

from typing import Literal, TypedDict

from openai.types.responses import Response as OpenAIResponse
from openai.types.responses.response_stream_event import ResponseStreamEvent
from pydantic import BaseModel


class ResponseUsage(BaseModel):
    """Usage statistics for an LLM response."""

    total_tokens: int
    prompt_tokens: int
    completion_tokens: int


class LLMResponse(BaseModel):
    """A response from an LLM."""

    output_text: str
    usage: ResponseUsage | None = None


class ResponseFormatText(TypedDict):
    """Text format configuration for responses."""

    format: Literal["text", "markdown", "json"]


ResponseFormat = ResponseFormatText | None

# Re-export OpenAI types that we use
__all__ = [
    "LLMResponse",
    "ResponseUsage",
    "ResponseFormat",
    "OpenAIResponse",
    "ResponseStreamEvent",
]
