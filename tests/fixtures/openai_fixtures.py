"""Fixtures for OpenAI tests."""

from typing import Any, AsyncGenerator
import pytest
from openai.types.responses import Response as OpenAIResponse
from openai.types.responses.response_output_message import ResponseOutputMessage
from openai.types.responses.response_output_text import ResponseOutputText
from alleycat_core.llm.openai import OpenAIConfig, OpenAIProvider
import os

@pytest.fixture
def openai_config() -> OpenAIConfig:
    """Create a test OpenAI configuration."""
    api_key = os.environ["ALLEYCAT_OPENAI_API_KEY"]
    return OpenAIConfig(api_key=api_key, model="gpt-4o-mini", temperature=0.7)


@pytest.fixture
def mock_openai_response() -> OpenAIResponse:
    """Create a mock OpenAI response.
    
    Returns a properly structured OpenAI response object with a simple text output.
    The response contains "42" as the output text, which is useful for basic testing.
    """
    message_content = ResponseOutputText(
        type="output_text",
        text="42",
        annotations=[]
    )

    message = ResponseOutputMessage(
        id="msg_123",
        content=[message_content],
        status="completed",
        role="assistant",
        type="message"
    )

    response_data = {
        "id": "mock-response-id",
        "created_at": 1234567890,
        "model": "gpt-4o-mini-mock",
        "object": "response",
        "output": [message],
        "status": "completed",
        "parallel_tool_calls": False,
        "tool_choice": "none",
        "tools": []
    }
    return OpenAIResponse.model_validate(response_data)


@pytest.fixture
async def mock_openai_client(mock_openai_response: OpenAIResponse, 
                           monkeypatch: pytest.MonkeyPatch) -> AsyncGenerator[OpenAIProvider, None]:
    """Create a mocked OpenAI client that returns a predefined response.
    
    Args:
        mock_openai_response: The response to return from the mocked client
        monkeypatch: pytest's monkeypatch fixture
        
    Returns:
        An OpenAIProvider instance with a mocked client that returns the mock response
    """
    config = OpenAIConfig(
        api_key="sk-test-key",
        model="gpt-4o-mini",
        temperature=0.7
    )
    provider = OpenAIProvider(config)

    async def mock_create(**kwargs: Any) -> OpenAIResponse:
        # Verify common parameters
        assert "input" in kwargs, "Input parameter is required"
        assert kwargs["model"] == config.model, "Model should match config"
        assert kwargs["temperature"] == config.temperature, "Temperature should match config"
        return mock_openai_response

    # Mock the create method of the responses client
    monkeypatch.setattr(provider.client.responses, "create", mock_create)

    yield provider 