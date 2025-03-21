"""Logging configuration for AlleyCat."""

from typing import Any

from rich.console import Console, ConsoleRenderable
from rich.theme import Theme

# Create themed console for logging
theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red bold",
        "success": "green",
        "debug": "grey70",
    }
)

# Console for verbose output (stderr)
verbose_console = Console(stderr=True, theme=theme)
# Console for errors (stderr)
error_console = Console(stderr=True, theme=theme)
# Console for normal output (stdout)
output_console = Console(theme=theme)

_verbose_enabled = False


def set_verbose(enabled: bool) -> None:
    """Enable or disable verbose output."""
    global _verbose_enabled
    _verbose_enabled = enabled


def is_verbose() -> bool:
    """Check if verbose output is enabled."""
    return _verbose_enabled


def info(message: str, **kwargs: Any) -> None:
    """Log an info message."""
    if _verbose_enabled:
        verbose_console.print(f"[info]ℹ [/info]{message}", **kwargs)


def warning(message: str, **kwargs: Any) -> None:
    """Log a warning message."""
    if _verbose_enabled:
        verbose_console.print(f"[warning]⚠ [/warning]{message}", **kwargs)


def error(message: str, **kwargs: Any) -> None:
    """Log an error message."""
    error_console.print(f"[error]✗ [/error]{message}", **kwargs)


def success(message: str, **kwargs: Any) -> None:
    """Log a success message."""
    if _verbose_enabled:
        verbose_console.print(f"[success]✓ [/success]{message}", **kwargs)


def debug(message: str, **kwargs: Any) -> None:
    """Log a debug message."""
    if _verbose_enabled:
        verbose_console.print(f"[debug]🔍 [/debug]{message}", **kwargs)


def output(message: str | ConsoleRenderable, **kwargs: Any) -> None:
    """Print output to stdout."""
    output_console.print(message, **kwargs)
