"""Tests for OpenAI provider implementation."""

import os
from typing import Any
import pytest
from openai.types.responses import Response as OpenAIResponse
from alleycat_core.llm.openai import OpenAIConfig, OpenAIFactory, OpenAIProvider


# Mark for tests that make external API calls
requires_api = pytest.mark.requires_api
skip_by_default = pytest.mark.skip(reason="Test makes external API calls. Run with --api to include")



def test_openai_factory():
    """Test OpenAI factory."""
    factory = OpenAIFactory()
    provider = factory.create(api_key=os.environ["ALLEYCAT_OPENAI_API_KEY"])

    assert isinstance(provider, OpenAIProvider)
    assert provider.config.api_key == os.environ["ALLEYCAT_OPENAI_API_KEY"]


@pytest.mark.asyncio
@requires_api
@skip_by_default
async def test_provider_respond_basic(openai_config: OpenAIConfig) -> None:
    """Test basic response functionality of OpenAIProvider.
    This test makes actual API calls to OpenAI.
    Run with --api flag to include this test.
    """
    provider = OpenAIProvider(openai_config)
    test_input = "Respond with the isolated number 42"

    response = await provider.respond(input=test_input)

    assert isinstance(response, OpenAIResponse)
    assert hasattr(response, "output")  # OpenAI response should have output attribute
    assert response.model.startswith(
        openai_config.model
    )  # Model should start with configured model name
    assert response.output_text == "42"  # Response should be as expected


@pytest.mark.asyncio
async def test_provider_respond_mocked(mock_openai_client: OpenAIProvider) -> None:
    """Test response functionality with mocked OpenAI client.
    Avoids making external API calls by mocking the client response.
    """
    test_input = "Respond with the isolated number 42"
    response = await mock_openai_client.respond(input=test_input)

    assert isinstance(response, OpenAIResponse)
    assert response.output_text == "42"
    assert response.model == "gpt-4o-mini-mock"
    assert response.status == "completed"

