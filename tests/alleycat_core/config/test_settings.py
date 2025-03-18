"""Unit tests for AlleyCat configuration settings."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from alleycat_core.config.settings import Settings

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture
def clean_env(monkeypatch: "MonkeyPatch") -> None:
    """Fixture to ensure a clean environment for settings tests."""
    # Clear all ALLEYCAT environment variables
    env_vars = [key for key in dict(os.environ) if key.startswith("ALLEYCAT_")]
    for env_var in env_vars:
        monkeypatch.delenv(env_var, raising=False)

    # Mock the existence of .env file
    monkeypatch.setattr(Path, "exists", lambda _: False)


def test_default_settings(clean_env: None) -> None:
    """Test that default settings are set correctly."""
    settings = Settings()

    assert settings.provider == "openai"
    # assert settings.openai_api_key == ""
    assert settings.model == "gpt-4o-mini"
    assert settings.temperature == 0.7
    assert settings.max_tokens is None
    assert settings.max_history == 100
    assert settings.output_format == "text"
    assert settings.history_file == Path.home() / ".alleycat" / "history.json"


def test_environment_override(monkeypatch: "MonkeyPatch") -> None:
    """Test that environment variables properly override default settings."""
    env_vars = {
        "ALLEYCAT_OPENAI_API_KEY": "test-key",
        "ALLEYCAT_MODEL": "gpt-4",
        "ALLEYCAT_TEMPERATURE": "0.5",
        "ALLEYCAT_MAX_TOKENS": "1000",
        "ALLEYCAT_OUTPUT_FORMAT": "markdown"
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    settings = Settings()

    assert settings.openai_api_key == "test-key"
    assert settings.model == "gpt-4"
    assert settings.temperature == 0.5
    assert settings.max_tokens == 1000
    assert settings.output_format == "markdown"


def test_temperature_validation() -> None:
    """Test that temperature validation works correctly."""
    with pytest.raises(ValidationError):
        Settings(temperature=-0.1)

    with pytest.raises(ValidationError):
        Settings(temperature=2.1)

    # Valid temperatures should not raise
    Settings(temperature=0.0)
    Settings(temperature=1.0)
    Settings(temperature=2.0)


def test_output_format_validation() -> None:
    """Test that output format validation works correctly."""
    with pytest.raises(ValidationError):
        Settings(output_format="invalid")

    # Valid formats should not raise
    Settings(output_format="text")
    Settings(output_format="markdown")
    Settings(output_format="json")


def test_provider_validation() -> None:
    """Test that provider validation works correctly."""
    with pytest.raises(ValidationError):
        Settings(provider="invalid")

    # Valid provider should not raise
    Settings(provider="openai")


def test_custom_history_file() -> None:
    """Test that custom history file path works correctly."""
    custom_path = Path("/tmp/test_history.json")
    settings = Settings(history_file=custom_path)
    assert settings.history_file == custom_path
