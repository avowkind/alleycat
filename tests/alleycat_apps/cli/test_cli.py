"""Tests for the AlleyCat CLI interface."""

import os
import pytest
from typer.testing import CliRunner
from unittest.mock import patch, AsyncMock

from alleycat_apps.cli.main import app
from alleycat_core.llm import Message, ChatResponse


@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    return CliRunner(env={
        "ALLEYCAT_OPENAI_API_KEY": "test-key",
        "ALLEYCAT_MODEL": "gpt-3.5-turbo",
        "ALLEYCAT_TEMPERATURE": "0.7",
        "ALLEYCAT_OUTPUT_FORMAT": "text"
    })


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    with patch("alleycat_core.llm.OpenAIFactory") as mock_factory:
        mock_llm = AsyncMock()
        mock_llm.complete.return_value = ChatResponse(
            content="This is a test response",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 5}
        )
        mock_factory.return_value.create.return_value = mock_llm
        yield mock_llm


def test_command_help(cli_runner):
    """Test the command help text."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Send a prompt to the LLM" in result.stdout


def test_command_basic(cli_runner, mock_llm):
    """Test basic command functionality."""
    result = cli_runner.invoke(app, ["Hello, how are you?"])
    assert result.exit_code == 0
    assert "This is a test response" in result.stdout
    mock_llm.complete.assert_called_once_with(
        [Message(role="user", content="Hello, how are you?")]
    )


def test_command_with_options(cli_runner, mock_llm):
    """Test command with various options."""
    result = cli_runner.invoke(
        app,
        [
            "--model", "gpt-4",
            "--temperature", "0.7",
            "--format", "markdown",
            "Tell me a joke"
        ]
    )
    assert result.exit_code == 0
    assert "This is a test response" in result.stdout
    mock_llm.complete.assert_called_once_with(
        [Message(role="user", content="Tell me a joke")]
    )


def test_command_invalid_format(cli_runner):
    """Test command with invalid format option."""
    result = cli_runner.invoke(
        app,
        [
            "--format", "invalid",
            "Hello"
        ]
    )
    assert result.exit_code != 0
    assert "Invalid value for '--format'" in result.stdout 