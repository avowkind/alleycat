"""Tests for OpenAI provider implementation."""

import os

import pytest

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
