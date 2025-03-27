"""Type definitions for LLM responses and events.

This module contains type definitions for LLM responses and events.

It uses the `pydantic.BaseModel` to define the types and the `openai.types.responses`
to define the types for the OpenAI API.

Author: Andrew Watkins <andrew@groat.nz>
"""

from typing import Any, Literal, TypedDict

from openai.types.responses import Response as OpenAIResponse
from openai.types.responses.response_stream_event import ResponseStreamEvent
from pydantic import BaseModel


class ResponseUsage(BaseModel):
    """Usage statistics for an LLM response."""

    total_tokens: int
    prompt_tokens: int
    completion_tokens: int


class ResponseFormatText(TypedDict):
    """Text format configuration for responses."""

    format: Literal["text", "markdown", "json", "schema"]


class ResponseFormatSchema(TypedDict):
    """Schema format configuration for responses."""

    type: Literal["json_schema"]
    name: str
    schema: dict[str, Any]
    strict: bool


class ResponseRefusal(TypedDict):
    """Response refusal information."""

    reason: str
    details: str | None


class LLMResponse(BaseModel):
    """A response from an LLM."""

    output_text: str
    usage: ResponseUsage | None = None
    refusal: ResponseRefusal | None = None


ResponseFormat = ResponseFormatText | ResponseFormatSchema | None

# Re-export OpenAI types that we use
__all__ = [
    "LLMResponse",
    "ResponseUsage",
    "ResponseFormat",
    "ResponseFormatSchema",
    "ResponseRefusal",
    "OpenAIResponse",
    "ResponseStreamEvent",
]
