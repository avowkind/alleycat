"""Tests for cursortest package."""

import cursortest


def test_version():
    """Test version is a string."""
    assert isinstance(cursortest.__version__, str) 