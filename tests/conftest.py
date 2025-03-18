"""Common test configuration and fixtures."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import load_dotenv

# Import fixtures to make them available to all tests
from .fixtures.openai_fixtures import (  # noqa: F401
    mock_openai_response,
    mock_openai_client,
    openai_config,
)


def pytest_configure():
    """Configure pytest - load environment variables before running tests."""
    load_dotenv()


@pytest.fixture(autouse=True)
def setup_test_env() -> Generator[None, None, None]:
    """Set up test environment."""
    # Store original environment
    original_env = dict(os.environ)

    # Get API key from environment, fail if not set
    api_key = os.environ.get("ALLEYCAT_OPENAI_API_KEY")
    if not api_key:
        pytest.fail(
            "ALLEYCAT_OPENAI_API_KEY environment variable must be set to run tests. "
            "Please set it to a valid OpenAI API key in your .env file."
        )
    # api_key = "sk-proj-1234567890" # fake for testing
    # Create temporary config directory
    test_config_dir = Path.home() / ".alleycat_test"
    test_config_dir.mkdir(exist_ok=True)

    # Set test environment variables
    os.environ["ALLEYCAT_OPENAI_API_KEY"] = api_key
    os.environ["ALLEYCAT_MODEL"] = "gpt-4o-mini"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

    # Clean up test directory
    if test_config_dir.exists():
        for file in test_config_dir.iterdir():
            file.unlink()
        test_config_dir.rmdir()


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--api",
        action="store_true",
        default=False,
        help="run tests that make API calls"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked as requiring API unless --api is specified."""
    if not config.getoption("--api"):
        skip_api = pytest.mark.skip(reason="need --api option to run tests that make API calls")
        for item in items:
            if "requires_api" in item.keywords:
                item.add_marker(skip_api)
