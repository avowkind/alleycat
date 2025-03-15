"""Tests for the CLI interface."""

from typer.testing import CliRunner

from cursortest.cli import app


def test_hello_command():
    """Test the hello command with various inputs."""
    runner = CliRunner()

    # Test with explicit name (with colors)
    result = runner.invoke(app, ["--name", "Test"])
    assert result.exit_code == 0
    assert "Hello" in result.stdout
    assert "Test" in result.stdout
    # Check for ANSI color codes and box drawing characters
    assert "\x1b[1;34m" in result.stdout  # bold blue
    assert "\x1b[1;32m" in result.stdout  # bold green
    assert "─" in result.stdout  # horizontal border
    assert "│" in result.stdout  # vertical border
    assert "Welcome" in result.stdout  # panel title

    # Test with no colors
    result = runner.invoke(app, ["--name", "Test", "--no-color"])
    assert result.exit_code == 0
    assert "Hello, Test! 👋" in result.stdout
    assert "\x1b[" not in result.stdout  # No ANSI codes
    assert "─" in result.stdout  # borders should still be present
    assert "│" in result.stdout

    # Test default behavior (will use "World")
    result = runner.invoke(app, input="\n")
    assert result.exit_code == 0
    assert "World" in result.stdout
    assert "Welcome" in result.stdout
