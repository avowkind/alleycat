"""Tests for OpenAI provider implementation."""

import os
from unittest import mock

import pytest
from pydantic import ValidationError

from alleycat_core.llm.openai import OpenAIConfig, OpenAIFactory, OpenAIProvider
from alleycat_core.llm.types import LLMResponse


def test_openai_factory() -> None:
    """Test OpenAI factory."""
    factory = OpenAIFactory()
    provider = factory.create(api_key=os.environ["ALLEYCAT_OPENAI_API_KEY"])

    assert isinstance(provider, OpenAIProvider)
    assert provider.config.api_key == os.environ["ALLEYCAT_OPENAI_API_KEY"]


@pytest.mark.asyncio
async def test_provider_respond_basic(openai_config: OpenAIConfig) -> None:
    """Test basic response functionality of OpenAIProvider.

    This test makes actual API calls to OpenAI.
    Run with --api flag to include this test.
    """
    provider = OpenAIProvider(openai_config)
    test_input = "Respond with the isolated number 42"

    response = await provider.respond(input=test_input)

    assert isinstance(response, LLMResponse)
    assert hasattr(response, "output_text")  # Response should have output_text attribute
    assert response.output_text == "42"  # Response should be as expected


@pytest.mark.asyncio
async def test_provider_respond_mocked(mock_openai_client: OpenAIProvider) -> None:
    """Test response functionality with mocked OpenAI client.

    Avoids making external API calls by mocking the client response.
    """
    test_input = "Respond with the isolated number 42"
    response = await mock_openai_client.respond(input=test_input)

    assert isinstance(response, LLMResponse)
    assert response.output_text == "42"


class TestOpenAIConfig:
    """Tests for OpenAIConfig."""

    def test_minimal_config(self) -> None:
        """Test minimal configuration."""
        config = OpenAIConfig(api_key="test-key")
        assert config.api_key == "test-key"
        assert config.model == "gpt-4o-mini"  # Default value
        assert config.temperature == 0.7  # Default value

    def test_full_config(self) -> None:
        """Test full configuration."""
        config = OpenAIConfig(
            api_key="test-key",
            model="gpt-4",
            temperature=0.5,
            max_tokens=100,
            response_format={"format": "json"},
            instructions="system instruction",
        )
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 100
        assert config.response_format == {"format": "json"}
        assert config.instructions == "system instruction"

    def test_temperature_validation(self) -> None:
        """Test temperature validation."""
        # Valid temperatures
        OpenAIConfig(api_key="test-key", temperature=0.0)
        OpenAIConfig(api_key="test-key", temperature=1.0)
        OpenAIConfig(api_key="test-key", temperature=2.0)

        # Invalid temperatures
        with pytest.raises(ValidationError):
            OpenAIConfig(api_key="test-key", temperature=-0.1)
        with pytest.raises(ValidationError):
            OpenAIConfig(api_key="test-key", temperature=2.1)


class TestOpenAIFactory:
    """Tests for OpenAIFactory."""

    def test_create_minimal(self) -> None:
        """Test create with minimal configuration."""
        factory = OpenAIFactory()
        provider = factory.create(api_key="test-key")
        assert isinstance(provider, OpenAIProvider)
        assert provider.config.api_key == "test-key"
        assert provider.config.model == "gpt-4o-mini"  # Default value

    def test_create_with_output_format(self) -> None:
        """Test create with output format."""
        factory = OpenAIFactory()
        provider = factory.create(api_key="test-key", output_format="json")
        assert isinstance(provider, OpenAIProvider)
        assert provider.config.response_format == {"format": "json"}


class TestOpenAIProvider:
    """Tests for OpenAIProvider."""

    def test_init(self) -> None:
        """Test initialization."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)
        assert provider.config == config
        assert provider.previous_response_id is None

    @pytest.mark.asyncio
    async def test_respond(self) -> None:
        """Test respond with minimum arguments."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        # Mock only the client.responses.create method
        provider.client = mock.AsyncMock()
        mock_response = mock.Mock()
        mock_response.output_text = "42"
        # Add other required attributes
        mock_response.id = "test-resp-id"
        mock_response.usage = None
        provider.client.responses.create.return_value = mock_response

        response = await provider.respond("test prompt")
        assert isinstance(response, LLMResponse)
        assert response.output_text == "42"
