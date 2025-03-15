"""Logging configuration for AlleyCat."""

from rich.console import Console
from rich.theme import Theme

# Create themed console for logging
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "debug": "grey70",
})

console = Console(theme=theme)
error_console = Console(stderr=True, theme=theme)

def info(message: str, **kwargs) -> None:
    """Log an info message."""
    console.print(f"[info]ℹ [/info]{message}", **kwargs)

def warning(message: str, **kwargs) -> None:
    """Log a warning message."""
    console.print(f"[warning]⚠ [/warning]{message}", **kwargs)

def error(message: str, **kwargs) -> None:
    """Log an error message."""
    error_console.print(f"[error]✗ [/error]{message}", **kwargs)

def success(message: str, **kwargs) -> None:
    """Log a success message."""
    console.print(f"[success]✓ [/success]{message}", **kwargs)

def debug(message: str, **kwargs) -> None:
    """Log a debug message."""
    console.print(f"[debug]🔍 [/debug]{message}", **kwargs) 