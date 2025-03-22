"""AlleyCat initialization command.

This module contains the command-line tool for initializing AlleyCat configuration.

Author: Andrew Watkins <andrew@groat.nz>
"""

import os
import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt

from alleycat_core.config.settings import Settings

console = Console()
app = typer.Typer(
    name="alleycat-init",
    help="Initialize AlleyCat configuration with interactive prompts",
    add_completion=True,
)


@app.command()
def main(
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove AlleyCat configuration and data files"),
) -> None:
    """Initialize AlleyCat configuration with interactive prompts.

    This command walks through setup questions and saves configuration to the
    XDG standard location (~/.config/alleycat/config.yml on Linux/macOS).

    If --remove is specified, it will remove the configuration file and other stored data.
    """
    # Create settings with defaults to get the paths
    settings = Settings()

    if remove:
        console.print("[bold]AlleyCat Configuration Removal[/bold]")
        console.print("This will remove AlleyCat configuration and data files.")
        console.print()

        # Display paths that will be removed
        if settings.config_file and settings.config_file.exists():
            console.print(f"Configuration file: [yellow]{settings.config_file}[/yellow]")

        if settings.history_file and settings.history_file.exists():
            console.print(f"History file: [yellow]{settings.history_file}[/yellow]")

        if settings.personas_dir and settings.personas_dir.exists():
            console.print(f"Personas directory: [yellow]{settings.personas_dir}[/yellow]")

        # Check if any files exist to remove
        files_exist = (
            (settings.config_file and settings.config_file.exists())
            or (settings.history_file and settings.history_file.exists())
            or (settings.personas_dir and settings.personas_dir.exists())
        )

        if not files_exist:
            console.print("[yellow]No configuration or data files found to remove.[/yellow]")
            return

        # Ask for confirmation
        if not Confirm.ask("\nAre you sure you want to remove these files?", default=False):
            console.print("Operation cancelled.")
            return

        # Remove files
        try:
            if settings.config_file and settings.config_file.exists():
                settings.config_file.unlink()
                console.print(f"Removed configuration file: [green]{settings.config_file}[/green]")

            if settings.history_file and settings.history_file.exists():
                settings.history_file.unlink()
                console.print(f"Removed history file: [green]{settings.history_file}[/green]")

            if settings.personas_dir and settings.personas_dir.exists():
                # Ask if personas should be removed
                if Confirm.ask("Remove persona files as well?", default=False):
                    shutil.rmtree(settings.personas_dir)
                    console.print(f"Removed personas directory: [green]{settings.personas_dir}[/green]")

            console.print("\n[bold green]AlleyCat configuration and data files have been removed.[/bold green]")
        except Exception as e:
            console.print(f"[bold red]Error removing files: {str(e)}[/bold red]")

        # Exit after removal
        return

    # Continue with normal initialization if not removing
    console.print("[bold]AlleyCat Configuration Setup[/bold]")
    console.print("This will create a configuration file at the standard location for your OS.")
    console.print()

    # Display configuration path
    console.print(f"Configuration will be saved to: [bold]{settings.config_file}[/bold]")
    console.print()

    # OpenAI API key
    current_key = settings.openai_api_key or os.environ.get("OPENAI_API_KEY", "")
    key_display = f"[dim]{current_key[:4]}...{current_key[-4:]}[/dim]" if current_key else "[dim]not set[/dim]"
    console.print(f"OpenAI API Key {key_display}")
    console.print(
        "Get your API key from: [link=https://platform.openai.com/api-keys]https://platform.openai.com/api-keys[/link]"
    )

    # Use input with masked characters rather than completely hidden
    console.print("Enter your OpenAI API key (input will be hidden for security)")
    new_key = Prompt.ask("API Key", password=True, default="")

    # Provide confirmation that input was received
    if new_key:
        # Show a masked version of the key
        masked_key = f"{new_key[:4]}...{new_key[-4:]}" if len(new_key) > 8 else "****"
        console.print(f"[green]API key received:[/green] [dim]{masked_key}[/dim]")
        settings.openai_api_key = new_key
    else:
        console.print("[yellow]No API key entered. Using existing key if available.[/yellow]")

    # Model selection
    models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
    console.print("\nAvailable models:")
    for i, model in enumerate(models, 1):
        console.print(f"  {i}. {model}")

    current_model_index = next((i for i, m in enumerate(models, 1) if m == settings.model), 2)  # Default to gpt-4o-mini
    model_choice = Prompt.ask(
        "Choose your preferred model",
        choices=[str(i) for i in range(1, len(models) + 1)],
        default=str(current_model_index),
    )
    settings.model = models[int(model_choice) - 1]

    # Temperature
    settings.temperature = float(
        Prompt.ask("\nSampling temperature (0.0-2.0, lower is more deterministic)", default=str(settings.temperature))
    )

    # Personas directory
    if settings.personas_dir:
        console.print(f"\nCurrent personas directory: [bold]{settings.personas_dir}[/bold]")

    personas_dir = Prompt.ask(
        "Enter a directory for persona instruction files",
        default=str(settings.personas_dir) if settings.personas_dir else "",
    )
    if personas_dir:
        settings.personas_dir = Path(personas_dir)
        # Create directory if it doesn't exist
        if not settings.personas_dir.exists():
            settings.personas_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"Created personas directory: [bold]{settings.personas_dir}[/bold]")

    # Web search
    enable_web = Prompt.ask(
        "\nEnable web search by default?", choices=["y", "n"], default="y" if settings.enable_web_search else "n"
    )
    settings.enable_web_search = enable_web.lower() == "y"

    # Save settings
    settings.save_to_file()
    console.print(f"\n[bold green]Configuration saved to {settings.config_file}[/bold green]")
    console.print("\nYou can now use AlleyCat with your configuration.")


if __name__ == "__main__":
    app()
