"""Tests for configuration settings."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from alleycat_core.config.settings import Settings


@pytest.fixture
def env_vars():
    """Set up test environment variables."""
    os.environ["ALLEYCAT_OPENAI_API_KEY"] = "test-key"
    os.environ["ALLEYCAT_MODEL"] = "gpt-4"
    os.environ["ALLEYCAT_TEMPERATURE"] = "0.8"
    yield
    del os.environ["ALLEYCAT_OPENAI_API_KEY"]
    del os.environ["ALLEYCAT_MODEL"]
    del os.environ["ALLEYCAT_TEMPERATURE"]


def test_default_settings():
    """Test default settings."""
    settings = Settings()
    assert settings.provider == "openai"
    assert settings.openai_api_key == ""
    assert settings.model == "gpt-3.5-turbo"
    assert settings.temperature == 0.7
    assert settings.max_tokens is None
    assert settings.output_format == "text"
    assert settings.max_history == 100
    assert isinstance(settings.history_file, Path)


def test_settings_from_env(env_vars):
    """Test settings from environment variables."""
    settings = Settings()
    assert settings.openai_api_key == "test-key"
    assert settings.model == "gpt-4"
    assert settings.temperature == 0.8


def test_settings_validation():
    """Test settings validation."""
    with pytest.raises(ValidationError):
        Settings(temperature=3.0)  # temperature must be <= 2.0
        
    with pytest.raises(ValidationError):
        Settings(temperature=-0.1)  # temperature must be >= 0.0
        
    with pytest.raises(ValidationError):
        Settings(output_format="invalid")  # must be text, markdown, or json


def test_settings_history_file():
    """Test history file path creation."""
    settings = Settings()
    assert settings.history_file.parent == Path.home() / ".alleycat"
    assert settings.history_file.name == "history.json" 