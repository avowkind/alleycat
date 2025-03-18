"""Tests for base LLM interfaces."""

import pytest
from pydantic import ValidationError

from alleycat_core.llm.base import Message


def test_message_creation() -> None:
    """Test creating a Message object."""
    message = Message(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"


def test_message_validation() -> None:
    """Test Message validation."""
    with pytest.raises(ValidationError):
        # Invalid type for content
        Message(role="user", content=123)  # type: ignore[arg-type]
