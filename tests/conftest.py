"""Common test configuration and fixtures."""

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from pytest import Config, Item, Parser

# Import fixtures to make them available to all tests
from .fixtures.cli_fixtures import cli_runner  # noqa: F401
from .fixtures.openai_fixtures import (  # noqa: F401
    mock_openai_client,
    mock_openai_response,
    openai_config,
)


def pytest_configure() -> None:
    """Configure pytest - load environment variables before running tests."""
    # Load .env file from current directory and project root
    load_dotenv()
    project_root = Path(__file__).parent.parent
    load_dotenv(project_root / ".env")


@pytest.fixture(autouse=True)
def setup_test_env() -> Generator[None, None, None]:
    """Set up test environment."""
    # Store original environment
    original_env = dict(os.environ)

    # Try to get API key from environment
    api_key = os.environ.get("ALLEYCAT_OPENAI_API_KEY")

    # If no API key found, try to load from .env file in project root
    if not api_key:
        project_root = Path(__file__).parent.parent
        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            api_key = os.environ.get("ALLEYCAT_OPENAI_API_KEY")

    # Use a mock key for testing if needed
    if not api_key:
        api_key = "sk-test-1234567890"  # Mock key for testing
        os.environ["ALLEYCAT_OPENAI_API_KEY"] = api_key
        print("Warning: Using mock API key for tests. Some tests may be skipped.")

    # Create temporary config directory for tests
    test_config_dir = Path.home() / ".config" / "alleycat_test"
    test_config_dir.mkdir(parents=True, exist_ok=True)

    # Set test environment variables
    os.environ["ALLEYCAT_MODEL"] = "gpt-4o-mini"
    os.environ["XDG_CONFIG_HOME"] = str(Path.home() / ".config" / "alleycat_test")

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

    # Clean up test directory
    if test_config_dir.exists():
        for file in test_config_dir.glob("**/*"):
            if file.is_file():
                file.unlink()
        for dir_path in sorted([p for p in test_config_dir.glob("**") if p.is_dir()], reverse=True):
            if dir_path.exists():
                try:
                    dir_path.rmdir()
                except (OSError, FileNotFoundError):
                    pass
        try:
            if test_config_dir.exists():
                test_config_dir.rmdir()
        except (OSError, FileNotFoundError):
            pass


def pytest_addoption(parser: Parser) -> None:
    """Add custom command line options."""
    parser.addoption("--api", action="store_true", default=False, help="run tests that make API calls")


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    """Skip tests marked as requiring API unless --api is specified."""
    if not config.getoption("--api"):
        skip_api = pytest.mark.skip(reason="need --api option to run tests that make API calls")
        for item in items:
            if "requires_api" in item.keywords:
                item.add_marker(skip_api)
