"""Tests for base LLM interfaces."""

import pytest
from pydantic import ValidationError

from alleycat_core.llm.base import ChatResponse, Message


def test_message_creation():
    """Test creating a Message object."""
    message = Message(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"


def test_message_validation():
    """Test Message validation."""
    with pytest.raises(ValidationError):
        Message(role="invalid", content=123)  # type: ignore


def test_chat_response_creation():
    """Test creating a ChatResponse object."""
    response = ChatResponse(
        content="Hello there!",
        finish_reason="stop",
        usage={"prompt_tokens": 10, "completion_tokens": 5}
    )
    assert response.content == "Hello there!"
    assert response.finish_reason == "stop"
    assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5}


def test_chat_response_optional_fields():
    """Test ChatResponse with optional fields."""
    response = ChatResponse(content="Hello!")
    assert response.content == "Hello!"
    assert response.finish_reason is None
    assert response.usage is None


def test_chat_response_validation():
    """Test ChatResponse validation."""
    with pytest.raises(ValidationError):
        ChatResponse(content=123)  # type: ignore 