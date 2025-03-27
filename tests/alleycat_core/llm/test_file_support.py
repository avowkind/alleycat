"""Tests for file support in OpenAI provider."""

from pathlib import Path
from unittest import mock

import pytest
from openai.types.file_object import FileObject

from alleycat_core.llm.openai import OpenAIConfig, OpenAIProvider


@pytest.fixture
def mock_async_openai_client() -> mock.AsyncMock:
    """Create a mock AsyncOpenAI client."""
    return mock.AsyncMock()


@pytest.mark.asyncio
async def test_file_upload_delete(mock_async_openai_client: mock.AsyncMock) -> None:
    """Test file upload and deletion."""
    # Create a sample file reference
    fixtures_path = Path(__file__).parent.parent.parent / "fixtures"
    sample_file_path = fixtures_path / "sample.pdf"

    # Skip test if file doesn't exist
    if not sample_file_path.exists():
        pytest.skip("Sample file not found")

    config = OpenAIConfig(api_key="test-key")
    provider = OpenAIProvider(config)
    provider.client = mock_async_openai_client

    # Mock the files.create response
    mock_file = mock.Mock(spec=FileObject)
    mock_file.id = "file-123456"
    mock_async_openai_client.files.create.return_value = mock_file

    # Mock the files.delete response
    mock_async_openai_client.files.delete.return_value = None

    # Test upload
    success = await provider.add_file(str(sample_file_path))
    assert success is True
    assert provider.remote_file is not None

    # Check that the client was called correctly
    mock_async_openai_client.files.create.assert_called_once()
    args, kwargs = mock_async_openai_client.files.create.call_args
    assert kwargs["purpose"] == "user_data"

    # Test cleanup
    result = await provider.cleanup_file()
    assert result is True
    assert provider.remote_file is None

    # Check that the client was called correctly
    mock_async_openai_client.files.delete.assert_called_once()


@pytest.mark.asyncio
async def test_respond_with_file(mock_async_openai_client: mock.AsyncMock) -> None:
    """Test respond method with a file attached."""
    config = OpenAIConfig(api_key="test-key")
    provider = OpenAIProvider(config)
    provider.client = mock_async_openai_client

    # Mock the responses.create response
    mock_response = mock.AsyncMock()
    mock_response.output_text = "This is a response referencing the file"
    mock_response.refusal = None
    mock_async_openai_client.responses.create.return_value = mock_response

    # Call the respond method
    file_path = Path(__file__).parent.parent.parent / "fixtures" / "sample.txt"
    await provider.add_file(str(file_path))
    await provider.respond("Analyze this file")

    # Check that the client was called with a properly structured input containing the file reference
    args, kwargs = mock_async_openai_client.responses.create.call_args
    assert "input" in kwargs

    # Verify the input is an array with one item
    input_array = kwargs["input"]
    assert isinstance(input_array, list)
    assert len(input_array) == 1

    # Verify the structured input format
    structured_input = input_array[0]
    assert isinstance(structured_input, dict)
    assert structured_input["role"] == "user"
    assert isinstance(structured_input["content"], list)

    # Verify file reference and text content
    content = structured_input["content"]
    assert len(content) == 2
    assert content[0]["type"] == "input_text"  # First item is file content
    assert content[1]["type"] == "input_text"  # Second item is user query


@pytest.mark.asyncio
async def test_respond_with_file_and_instructions(mock_async_openai_client: mock.AsyncMock) -> None:
    """Test respond method with a file attached and instructions."""
    config = OpenAIConfig(api_key="test-key")
    provider = OpenAIProvider(config)
    provider.client = mock_async_openai_client

    # Mock the responses.create response
    mock_response = mock.AsyncMock()
    mock_response.output_text = "This is a response referencing the file"
    mock_response.refusal = None
    mock_async_openai_client.responses.create.return_value = mock_response

    # Call the respond method with instructions
    original_instructions = "Act as a helpful assistant."
    await provider.respond("Analyze this file", instructions=original_instructions)

    # Check that the client was called with a properly structured input containing the file reference
    args, kwargs = mock_async_openai_client.responses.create.call_args

    # Verify the input is structured correctly
    assert "input" in kwargs
    assert isinstance(kwargs["input"], list)

    # Verify instructions were preserved and enhanced
    assert "instructions" in kwargs
    assert original_instructions in kwargs["instructions"]
    assert "Act as a helpful assistant" in kwargs["instructions"]
