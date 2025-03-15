"""Command line interface for cursortest."""
import os

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Ensure color support in virtual environments
os.environ["FORCE_COLOR"] = "1"
os.environ["TERM"] = os.environ.get("TERM", "xterm-256color")

# Create console with explicit color settings
console = Console(
    force_terminal=True,
    color_system="auto",
    highlight=True,
    emoji=True
)

app = typer.Typer(
    help="A friendly CLI that demonstrates modern Python CLI development",
    add_completion=True,
    pretty_exceptions_enable=False,  # Disable Typer's exception handling to use Rich's
)


@app.command()
def hello(
    name: str | None = typer.Option(
        None,
        "--name",
        "-n",
        help="The name of the person to greet",
        prompt="What's your name?",
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output",
    ),
) -> None:
    """Say hello to someone in style!

    If no name is provided, it will prompt for one.
    """
    # Create console based on color preference
    output_console = Console(
        force_terminal=not no_color,
        color_system="auto" if not no_color else None,
        highlight=not no_color,
        emoji=True
    )

    greeting = Text()
    greeting.append("Hello, ", style="bold blue")
    greeting.append(f"{name or 'World'}", style="bold green")
    greeting.append("! 👋", style="bold blue")

    # Create a panel with the greeting
    panel = Panel(
        greeting,
        title="Welcome",
        border_style="blue",
        padding=(1, 2),
    )

    output_console.print(panel)


if __name__ == "__main__":
    app()
