"""Common test configuration and fixtures."""

import os
from pathlib import Path
from typing import Generator

import pytest
from dotenv import load_dotenv


def pytest_configure():
    """Configure pytest - load environment variables before running tests."""
    load_dotenv()


@pytest.fixture(autouse=True)
def setup_test_env() -> Generator[None, None, None]:
    """Set up test environment."""
    # Store original environment
    original_env = dict(os.environ)
    
    # Get API key from environment, fail if not set
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        pytest.fail(
            "OPENAI_API_KEY environment variable must be set to run tests. "
            "Please set it to a valid OpenAI API key in your .env file."
        )
    
    # Create temporary config directory
    test_config_dir = Path.home() / ".alleycat_test"
    test_config_dir.mkdir(exist_ok=True)
    
    # Set test environment variables
    os.environ["ALLEYCAT_OPENAI_API_KEY"] = api_key
    os.environ["ALLEYCAT_MODEL"] = "gpt-3.5-turbo"
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)
    
    # Clean up test directory
    if test_config_dir.exists():
        for file in test_config_dir.iterdir():
            file.unlink()
        test_config_dir.rmdir() 