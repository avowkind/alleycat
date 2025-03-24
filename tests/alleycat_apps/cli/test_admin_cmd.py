"""Tests for the admin CLI command.

This module contains tests for the admin CLI command, focusing on KB operations.

Author: Andrew Watkins <andrew@groat.nz>
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

# Ignore missing stubs
from alleycat_apps.cli.admin_cmd import app  # type: ignore
from alleycat_core.config.settings import Settings  # type: ignore


@pytest.fixture
def mock_settings(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Mock Settings class."""
    mock = MagicMock(spec=Settings)
    mock.knowledge_bases = {}
    mock.kb_files = {}
    mock.default_kb = None
    mock.openai_api_key = "test-api-key"
    mock.config_file = Path("/tmp/config.yml")

    # Mock the save_to_file and load_from_file methods
    mock.save_to_file.return_value = None
    mock.load_from_file.return_value = None

    # Patch the Settings class
    monkeypatch.setattr("alleycat_apps.cli.admin_cmd.Settings", lambda: mock)

    return mock


@pytest.fixture
def mock_kb_provider(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Mock KB provider."""
    mock = AsyncMock()

    # Setup common return values
    mock.create_vector_store.return_value = {
        "id": "vs_test123",
        "name": "test-kb",
        "created_at": "2023-01-01T00:00:00Z",
        "metadata": {"name": "test-kb"},
    }

    mock.list_vector_stores.return_value = [
        {"id": "vs_test123", "name": "test-kb", "created_at": "2023-01-01T00:00:00Z", "metadata": {"name": "test-kb"}}
    ]

    mock.get_vector_store.return_value = {
        "id": "vs_test123",
        "name": "test-kb",
        "created_at": "2023-01-01T00:00:00Z",
        "metadata": {"name": "test-kb"},
    }

    mock.delete_vector_store.return_value = True

    mock.add_files.return_value = [
        {"file_id": "file_test123", "file_path": "/tmp/test.txt", "batch_id": "batch_test123"}
    ]

    mock.list_files.return_value = [
        {"id": "file_test123", "created_at": "2023-01-01T00:00:00Z", "object": "vector-store-file"}
    ]

    mock.delete_file.return_value = True

    # Patch the get_kb_provider function
    async def mock_get_provider(settings: Any) -> AsyncMock:
        return mock

    monkeypatch.setattr("alleycat_apps.cli.admin_cmd.get_kb_provider", mock_get_provider)

    return mock


@pytest.fixture
def runner() -> CliRunner:
    """Get a CLI runner."""
    return CliRunner()


def test_kb_create(runner: CliRunner, mock_settings: MagicMock, mock_kb_provider: AsyncMock) -> None:
    """Test the 'kb create' command."""
    # Run the command
    result = runner.invoke(app, ["kb", "create", "test-kb"])

    # Check the result
    assert result.exit_code == 0
    assert "Created knowledge base 'test-kb'" in result.stdout

    # Check that the KB provider was called correctly
    mock_kb_provider.create_vector_store.assert_called_once_with(name="test-kb")

    # Check that settings were updated
    assert mock_settings.knowledge_bases == {"test-kb": "vs_test123"}
    assert mock_settings.kb_files == {"vs_test123": {}}
    assert mock_settings.default_kb == "test-kb"
    mock_settings.save_to_file.assert_called_once()


def test_kb_ls_all(runner: CliRunner, mock_settings: MagicMock, mock_kb_provider: AsyncMock) -> None:
    """Test the 'kb ls' command with no arguments."""
    # Setup mocks
    mock_settings.knowledge_bases = {"test-kb": "vs_test123"}
    mock_settings.default_kb = "test-kb"

    # Run the command
    result = runner.invoke(app, ["kb", "ls"])

    # Check the result
    assert result.exit_code == 0
    assert "Knowledge Bases:" in result.stdout
    assert "test-kb" in result.stdout
    assert "vs_test123" in result.stdout
    assert "(default)" in result.stdout

    # KB provider should not have been called for listing all KBs
    mock_kb_provider.list_vector_stores.assert_not_called()


def test_kb_ls_specific(runner: CliRunner, mock_settings: MagicMock, mock_kb_provider: AsyncMock) -> None:
    """Test the 'kb ls' command with a specific KB."""
    # Setup mocks
    mock_settings.knowledge_bases = {"test-kb": "vs_test123"}
    mock_settings.kb_files = {"vs_test123": {"file_test123": "/tmp/test.txt"}}

    # Run the command
    result = runner.invoke(app, ["kb", "ls", "--name", "test-kb"])

    # Check the result
    assert result.exit_code == 0
    assert "Files in knowledge base 'test-kb':" in result.stdout
    assert "/tmp/test.txt" in result.stdout
    assert "file_test123" in result.stdout

    # KB provider should have been called to list files
    mock_kb_provider.list_files.assert_called_once_with("vs_test123")


def test_kb_rm(runner: CliRunner, mock_settings: MagicMock, mock_kb_provider: AsyncMock) -> None:
    """Test the 'kb rm' command."""
    # Setup mocks
    mock_settings.knowledge_bases = {"test-kb": "vs_test123"}
    mock_settings.kb_files = {"vs_test123": {"file_test123": "/tmp/test.txt"}}
    mock_settings.default_kb = "test-kb"

    # Run the command with --force to skip confirmation
    result = runner.invoke(app, ["kb", "rm", "test-kb", "--force"])

    # Check the result
    assert result.exit_code == 0
    assert "Removed knowledge base 'test-kb'" in result.stdout

    # KB provider should have been called to delete the vector store
    mock_kb_provider.delete_vector_store.assert_called_once_with("vs_test123")

    # Check that settings were updated
    assert mock_settings.knowledge_bases == {}
    assert "vs_test123" not in mock_settings.kb_files
    assert mock_settings.default_kb is None
    mock_settings.save_to_file.assert_called_once()


def test_kb_add_files(runner: CliRunner, mock_settings: MagicMock, mock_kb_provider: AsyncMock, tmp_path: Path) -> None:
    """Test the 'kb add' command."""
    # Setup mocks
    mock_settings.knowledge_bases = {"test-kb": "vs_test123"}
    mock_settings.kb_files = {"vs_test123": {}}

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is a test file")

    # Use monkeypatch to override the confirmation prompt
    with patch("alleycat_apps.cli.admin_cmd.Confirm.ask", return_value=True):
        # Run the command
        result = runner.invoke(app, ["kb", "add", "test-kb", str(test_file)])

    # Check the result
    assert result.exit_code == 0
    assert "Added 1 files to knowledge base 'test-kb'" in result.stdout

    # KB provider should have been called to add files
    mock_kb_provider.add_files.assert_called_once()
    # Check the file path was correctly passed (uses Path objects)
    args, kwargs = mock_kb_provider.add_files.call_args
    assert args[0] == "vs_test123"
    assert len(args[1]) == 1
    assert str(args[1][0]) == str(test_file)

    # Check settings were updated
    assert mock_settings.kb_files["vs_test123"] == {"file_test123": "/tmp/test.txt"}
    mock_settings.save_to_file.assert_called_once()


def test_kb_delete_file(runner: CliRunner, mock_settings: MagicMock, mock_kb_provider: AsyncMock) -> None:
    """Test the 'kb delete' command."""
    # Setup mocks
    mock_settings.knowledge_bases = {"test-kb": "vs_test123"}
    mock_settings.kb_files = {"vs_test123": {"file_test123": "/tmp/test.txt"}}

    # Run the command
    result = runner.invoke(app, ["kb", "delete", "test-kb", "file_test123"])

    # Check the result
    assert result.exit_code == 0
    assert "Removed file 'file_test123' from knowledge base 'test-kb'" in result.stdout

    # KB provider should have been called to delete the file
    mock_kb_provider.delete_file.assert_called_once_with("vs_test123", "file_test123")

    # Check settings were updated
    assert "file_test123" not in mock_settings.kb_files["vs_test123"]
    mock_settings.save_to_file.assert_called_once()
