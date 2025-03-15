"""Tests for OpenAI provider implementation."""

import os
from collections.abc import AsyncIterator

import pytest
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion import Choice as ChunkChoice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from alleycat_core.llm.base import Message
from alleycat_core.llm.openai import OpenAIConfig, OpenAIFactory, OpenAIProvider


@pytest.fixture
def openai_config() -> OpenAIConfig:
    """Create a test OpenAI configuration."""
    api_key = os.environ["ALLEYCAT_OPENAI_API_KEY"]
    return OpenAIConfig(
        api_key=api_key,
        model="gpt-3.5-turbo",
        temperature=0.7
    )


@pytest.fixture
def mock_openai_response(mocker):
    """Create a mock OpenAI API response."""
    return ChatCompletion(
        id="test-id",
        model="gpt-3.5-turbo",
        object="chat.completion",
        created=1234567890,
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content="Test response",
                    role="assistant"
                )
            )
        ],
        usage=CompletionUsage(
            completion_tokens=5,
            prompt_tokens=10,
            total_tokens=15
        )
    )


@pytest.fixture
def mock_openai_stream(mocker):
    """Create a mock OpenAI API streaming response."""
    async def mock_stream() -> AsyncIterator[ChatCompletionChunk]:
        yield ChatCompletionChunk(
            id="test-id",
            model="gpt-3.5-turbo",
            object="chat.completion.chunk",
            created=1234567890,
            choices=[
                ChunkChoice(
                    delta=ChatCompletionMessage(
                        content="Test ",
                        role="assistant"
                    ),
                    finish_reason=None,
                    index=0
                )
            ]
        )
        yield ChatCompletionChunk(
            id="test-id",
            model="gpt-3.5-turbo",
            object="chat.completion.chunk",
            created=1234567890,
            choices=[
                ChunkChoice(
                    delta=ChatCompletionMessage(
                        content="response",
                        role=None
                    ),
                    finish_reason="stop",
                    index=0
                )
            ]
        )
    return mock_stream()


def test_openai_config():
    """Test OpenAI configuration."""
    config = OpenAIConfig(api_key="test-key")
    assert config.api_key == "test-key"
    assert config.model == "gpt-3.5-turbo"  # default value
    assert config.temperature == 0.7  # default value
    assert config.max_tokens is None  # default value


def test_openai_provider_init(openai_config):
    """Test OpenAI provider initialization."""
    provider = OpenAIProvider(openai_config)
    assert provider.config == openai_config
    assert provider.client.api_key == openai_config.api_key


@pytest.mark.asyncio
async def test_openai_provider_complete(
    openai_config, mock_openai_response, mocker
):
    """Test OpenAI provider completion."""
    mock_create = mocker.patch(
        "openai.resources.chat.completions.Completions.create",
        return_value=mock_openai_response
    )

    provider = OpenAIProvider(openai_config)
    messages = [Message(role="user", content="Hello")]

    response = await provider.complete(messages)

    assert response.content == "Test response"
    assert response.finish_reason == "stop"
    assert response.usage == {
        "completion_tokens": 5,
        "prompt_tokens": 10,
        "total_tokens": 15
    }

    mock_create.assert_called_once_with(
        model=openai_config.model,
        messages=[{"role": "user", "content": "Hello"}],
        temperature=openai_config.temperature,
        max_tokens=None,
        stream=False
    )


@pytest.mark.asyncio
async def test_openai_provider_complete_stream(
    openai_config, mock_openai_stream, mocker
):
    """Test OpenAI provider streaming completion."""
    mocker.patch(
        "openai.resources.chat.completions.Completions.create",
        return_value=mock_openai_stream
    )

    provider = OpenAIProvider(openai_config)
    messages = [Message(role="user", content="Hello")]

    chunks = []
    async for chunk in provider.complete_stream(messages):
        chunks.append(chunk)

    assert len(chunks) == 2
    assert chunks[0].content == "Test "
    assert chunks[0].finish_reason is None
    assert chunks[1].content == "response"
    assert chunks[1].finish_reason == "stop"


def test_openai_factory():
    """Test OpenAI factory."""
    factory = OpenAIFactory()
    provider = factory.create(api_key=os.environ["ALLEYCAT_OPENAI_API_KEY"])

    assert isinstance(provider, OpenAIProvider)
    assert provider.config.api_key == os.environ["ALLEYCAT_OPENAI_API_KEY"]
