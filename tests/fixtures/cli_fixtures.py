"""CLI-related test fixtures."""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner(
        env={
            "ALLEYCAT_MODEL": "gpt-4o-mini",
            "ALLEYCAT_TEMPERATURE": "0.7",
            "ALLEYCAT_OUTPUT_FORMAT": "text",
            "ALLEYCAT_PROVIDER": "openai",
        }
    )
