"""Tests for OpenAI provider implementation."""

import os
from pathlib import Path
from unittest import mock

import pytest
from pydantic import ValidationError

from alleycat_core.llm.openai import OpenAIConfig, OpenAIFactory, OpenAIProvider
from alleycat_core.llm.remote_file import RemoteFile, TextFile, UploadedFile
from alleycat_core.llm.types import LLMResponse


def test_openai_factory() -> None:
    """Test OpenAI factory."""
    factory = OpenAIFactory()
    provider = factory.create(api_key=os.environ["ALLEYCAT_OPENAI_API_KEY"])

    assert isinstance(provider, OpenAIProvider)
    assert provider.config.api_key == os.environ["ALLEYCAT_OPENAI_API_KEY"]


@pytest.mark.asyncio
@pytest.mark.requires_api
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
        assert provider.remote_file is None

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
        # Set refusal attributes to None to avoid validation errors
        mock_response.refusal = None
        provider.client.responses.create.return_value = mock_response

        response = await provider.respond("test prompt")
        assert isinstance(response, LLMResponse)
        assert response.output_text == "42"

    @pytest.mark.asyncio
    async def test_setup_text_file(self) -> None:
        """Test setting up a text file."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        # Create a temp test file
        test_dir = Path(__file__).parent / "test_files"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test.txt"
        test_file.write_text("Test content")

        try:
            # Setup the file
            with mock.patch("alleycat_core.llm.remote_file.TextFile.initialize") as mock_init:
                mock_init.return_value = True
                success = await provider.add_file(str(test_file))
                assert success
                assert provider.remote_file is not None
                assert isinstance(provider.remote_file, TextFile)
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
            if test_dir.exists() and not list(test_dir.iterdir()):
                test_dir.rmdir()

    @pytest.mark.asyncio
    async def test_setup_binary_file(self) -> None:
        """Test setting up a binary file that should be uploaded."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        # Create a temp test file
        test_dir = Path(__file__).parent / "test_files"
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "test.pdf"
        test_file.write_text("Test PDF content")

        try:
            # Setup the file
            with mock.patch("alleycat_core.llm.remote_file.UploadedFile.initialize") as mock_init:
                mock_init.return_value = True
                success = await provider.add_file(str(test_file))
                assert success
                assert provider.remote_file is not None
                assert isinstance(provider.remote_file, UploadedFile)
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()
            if test_dir.exists() and not list(test_dir.iterdir()):
                test_dir.rmdir()

    @pytest.mark.asyncio
    async def test_cleanup_file(self) -> None:
        """Test cleaning up a file."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        # Mock a remote file
        mock_remote_file = mock.AsyncMock(spec=RemoteFile)
        mock_remote_file.cleanup.return_value = True
        provider.remote_file = mock_remote_file

        # Clean up the file
        success = await provider.cleanup_file()
        assert success
        assert provider.remote_file is None
        mock_remote_file.cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_respond_with_text_file(self) -> None:
        """Test responding with a text file."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        # Mock client and text file
        provider.client = mock.AsyncMock()
        mock_response = mock.Mock()
        mock_response.output_text = "Analysis of the text file"
        mock_response.id = "test-resp-id"
        mock_response.usage = None
        mock_response.refusal = None
        provider.client.responses.create.return_value = mock_response

        # Mock text file and its methods
        mock_text_file = mock.AsyncMock(spec=TextFile)
        mock_text_file.get_file_prompt.return_value = {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "File content"},
                {"type": "input_text", "text": "Analyze this file"},
            ],
        }
        mock_text_file.get_file_context.return_value = {}  # Return empty dict for file context
        provider.remote_file = mock_text_file

        # Get response
        response = await provider.respond("Analyze this file")
        assert isinstance(response, LLMResponse)
        assert response.output_text == "Analysis of the text file"

    @pytest.mark.asyncio
    async def test_respond_with_uploaded_file(self) -> None:
        """Test responding with an uploaded file."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)

        # Mock client and uploaded file
        provider.client = mock.AsyncMock()
        mock_response = mock.Mock()
        mock_response.output_text = "Analysis of the PDF"
        mock_response.id = "test-resp-id"
        mock_response.usage = None
        mock_response.refusal = None
        provider.client.responses.create.return_value = mock_response

        # Mock uploaded file and its methods
        mock_uploaded_file = mock.AsyncMock(spec=UploadedFile)
        mock_uploaded_file.get_file_prompt.return_value = {
            "role": "user",
            "content": [
                {"type": "input_file", "file_id": "test-file-id"},
                {"type": "input_text", "text": "Analyze this file"},
            ],
        }
        mock_uploaded_file.get_file_context.return_value = {}  # Return empty dict for file context
        provider.remote_file = mock_uploaded_file

        # Get response
        response = await provider.respond("Analyze this file")
        assert isinstance(response, LLMResponse)
        assert response.output_text == "Analysis of the PDF"
