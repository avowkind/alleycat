"""Tests for the OpenAI KB provider.

This module contains tests for the OpenAI KB provider.

Author: Andrew Watkins <andrew@groat.nz>
"""

import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio

from alleycat_core.kb import OpenAIKBFactory, OpenAIKBProvider

# Skip all tests in this module if the API key is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY environment variable not set",
)


@pytest_asyncio.fixture
async def openai_kb_provider() -> AsyncGenerator[OpenAIKBProvider, None]:
    """Create an OpenAI KB provider instance.

    This fixture creates a real OpenAI KB provider instance for testing.
    It requires the OPENAI_API_KEY environment variable to be set.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    factory = OpenAIKBFactory()
    provider = factory.create(api_key=api_key)

    # Cast to the correct type since we know this is the concrete implementation
    typed_provider = provider if isinstance(provider, OpenAIKBProvider) else None
    assert typed_provider is not None, "Factory did not create an OpenAIKBProvider instance"

    try:
        yield typed_provider
    finally:
        await typed_provider.close()


@pytest.mark.requires_api
@pytest.mark.asyncio
async def test_create_vector_store(openai_kb_provider: OpenAIKBProvider) -> None:
    """Test creating a vector store."""
    # Create a vector store with a unique name
    name = f"test-vector-store-{os.urandom(4).hex()}"
    result = await openai_kb_provider.create_vector_store(name=name)

    # Verify the result
    assert "id" in result
    assert result["name"] == name
    assert "created_at" in result
    assert "metadata" in result
    assert result["metadata"]["name"] == name

    # Clean up - delete the vector store
    vector_store_id = result["id"]
    delete_result = await openai_kb_provider.delete_vector_store(vector_store_id)
    assert delete_result is True


@pytest.mark.requires_api
@pytest.mark.asyncio
async def test_list_vector_stores(openai_kb_provider: OpenAIKBProvider) -> None:
    """Test listing vector stores."""
    # Create a vector store
    name = f"test-vector-store-list-{os.urandom(4).hex()}"
    create_result = await openai_kb_provider.create_vector_store(name=name)
    vector_store_id = create_result["id"]

    try:
        # List vector stores
        result = await openai_kb_provider.list_vector_stores()

        # Verify the result
        assert isinstance(result, list)
        assert len(result) > 0

        # Check if our created vector store is in the list
        found = False
        for vs in result:
            if vs["id"] == vector_store_id:
                found = True
                assert vs["name"] == name
                break

        assert found, f"Created vector store {vector_store_id} not found in list"
    finally:
        # Clean up
        await openai_kb_provider.delete_vector_store(vector_store_id)


@pytest.mark.requires_api
@pytest.mark.asyncio
async def test_get_vector_store(openai_kb_provider: OpenAIKBProvider) -> None:
    """Test getting a vector store."""
    # Create a vector store
    name = f"test-vector-store-get-{os.urandom(4).hex()}"
    create_result = await openai_kb_provider.create_vector_store(name=name)
    vector_store_id = create_result["id"]

    try:
        # Get the vector store
        result = await openai_kb_provider.get_vector_store(vector_store_id)

        # Verify the result
        assert result["id"] == vector_store_id
        assert result["name"] == name
        assert "created_at" in result
        assert "metadata" in result
    finally:
        # Clean up
        await openai_kb_provider.delete_vector_store(vector_store_id)


@pytest.mark.requires_api
@pytest.mark.asyncio
async def test_file_operations(openai_kb_provider: OpenAIKBProvider, tmp_path: Path) -> None:
    """Test file operations."""
    # Create a vector store
    name = f"test-vector-store-files-{os.urandom(4).hex()}"
    create_result = await openai_kb_provider.create_vector_store(name=name)
    vector_store_id = create_result["id"]

    try:
        # Create a test file
        file_path = tmp_path / "test_file.txt"
        file_path.write_text("This is a test file for vector store testing.")

        # Add the file to the vector store
        add_result = await openai_kb_provider.add_files(vector_store_id, [file_path])

        # Verify the result
        assert isinstance(add_result, list)
        assert len(add_result) == 1
        assert "file_id" in add_result[0]
        assert "batch_id" in add_result[0]

        file_id = add_result[0]["file_id"]

        # List files in the vector store
        list_result = await openai_kb_provider.list_files(vector_store_id)

        # Verify the result
        assert isinstance(list_result, list)

        # Note: There might be a delay between adding and listing files
        # Therefore, we might not find the file immediately
        # This is a real API limitation

        # Delete the file from the vector store
        delete_result = await openai_kb_provider.delete_file(vector_store_id, file_id)
        assert delete_result is True
    finally:
        # Clean up
        await openai_kb_provider.delete_vector_store(vector_store_id)
