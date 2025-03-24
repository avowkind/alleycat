"""Alleycat admin CLI command.

This module provides administrative commands for Alleycat, particularly for
managing knowledge bases.

Author: Andrew Watkins <andrew@groat.nz>
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from alleycat_core import logging as alleycat_logging
from alleycat_core.config.settings import Settings
from alleycat_core.kb.provider import get_kb_provider

app = typer.Typer(
    help="Alleycat admin commands",
    no_args_is_help=True,
    add_completion=False,
)
kb_app = typer.Typer(
    help="Knowledge base commands",
    no_args_is_help=True,
)
app.add_typer(kb_app, name="kb")

console = Console()

# Common options
verbose_option = typer.Option(False, "--verbose", "-v", help="Enable verbose debug output")

# Define arguments at module level
kb_add_file_paths_arg = typer.Argument(..., help="Paths to files to add")


@app.callback()
def main(verbose: bool = verbose_option) -> None:
    """AlleyCat admin CLI."""
    if verbose:
        alleycat_logging.set_verbose(True)


# Add setup command for backward compatibility
@app.command("setup", help="Initialize Alleycat configuration")
def setup_cmd(remove: bool = typer.Option(False, "--remove", "-r", help="Remove the configuration")) -> None:
    """Initialize Alleycat configuration."""
    if remove:
        _remove_config()
    else:
        _init_config()


def _remove_config() -> None:
    """Remove the configuration file."""
    settings = Settings()

    if settings.config_file and Path(settings.config_file).exists():
        if Confirm.ask(f"Remove configuration file at {settings.config_file}?"):
            Path(settings.config_file).unlink()
            console.print("[green]Configuration file removed.[/green]")
        else:
            console.print("[yellow]Removal cancelled.[/yellow]")
    else:
        console.print("[yellow]No configuration file found.[/yellow]")


def _init_config() -> None:
    """Initialize the configuration file."""
    settings = Settings()

    # Check if configuration already exists
    if settings.config_file and Path(settings.config_file).exists():
        if not Confirm.ask(f"Configuration file already exists at {settings.config_file}. Overwrite?"):
            console.print("[yellow]Setup cancelled.[/yellow]")
            return

    # Get OpenAI API key
    api_key = Prompt.ask("Enter your OpenAI API key", password=True)
    if not api_key:
        console.print("[red]No API key provided, setup cancelled.[/red]")
        return

    # Update settings
    settings.openai_api_key = api_key
    settings.save_to_file()

    console.print(f"[green]Configuration saved to {settings.config_file}[/green]")


@kb_app.callback()
def kb_main(verbose: bool = verbose_option) -> None:
    """Knowledge base management commands."""
    if verbose:
        alleycat_logging.set_verbose(True)


@kb_app.command("create", help="Create a new knowledge base")
def kb_create(name: str, verbose: bool = verbose_option) -> None:
    """Create a new knowledge base."""
    if verbose:
        alleycat_logging.set_verbose(True)

    settings = Settings()

    # Check if the KB already exists
    if name in settings.knowledge_bases:
        console.print(f"[red]Knowledge base '{name}' already exists[/red]")
        return

    try:
        # Create the vector store
        result = asyncio.run(_create_vector_store(name, settings))
        vs_id = result["id"]

        # Update settings
        settings.knowledge_bases[name] = vs_id
        settings.kb_files[vs_id] = {}

        # Set as default if it's the first KB
        if settings.default_kb is None:
            settings.default_kb = name

        # Save settings
        settings.save_to_file()

        console.print(f"[green]Created knowledge base '{name}'[/green]")
        console.print(f"Vector store ID: {vs_id}")
        if settings.default_kb == name:
            console.print("Set as default knowledge base")

    except Exception as e:
        console.print(f"[red]Error creating knowledge base: {e}[/red]")


async def _create_vector_store(name: str, settings: Settings) -> dict[str, Any]:
    """Create a vector store for the knowledge base."""
    provider = await get_kb_provider(settings)
    result = await provider.create_vector_store(name=name)
    await provider.close()
    return result


@kb_app.command("ls", help="List knowledge bases or files in a knowledge base")
def kb_ls(
    name: str | None = typer.Option(None, "--name", help="Name of knowledge base to list files for"),
    verbose: bool = verbose_option,
) -> None:
    """List knowledge bases or files in a knowledge base."""
    if verbose:
        alleycat_logging.set_verbose(True)

    settings = Settings()

    # If no name provided, list all KBs
    if name is None:
        _list_all_kbs(settings)
        return

    # Check if the KB exists
    if name not in settings.knowledge_bases:
        console.print(f"[red]Knowledge base '{name}' does not exist[/red]")
        return

    # Get the vector store ID
    vs_id = settings.knowledge_bases[name]

    try:
        # List files in the KB
        files = asyncio.run(_list_kb_files(vs_id, settings))

        # Create a table to display the files
        table = Table(title=f"Files in knowledge base '{name}':")
        table.add_column("File ID", style="cyan")
        table.add_column("File Path", style="green")
        table.add_column("Status", style="yellow")

        # Get existing file paths from settings
        kb_files_dict = dict(settings.kb_files)
        vs_files = kb_files_dict.get(vs_id, {})

        # Check if we need to update file information
        unknown_files = False
        for file in files:
            file_id = file["id"]
            if file_id not in vs_files:
                unknown_files = True
                break

        # Update file information if needed
        if unknown_files:
            console.print("[yellow]Found files without path information. Updating settings...[/yellow]")

            # Ensure the vs_id exists in kb_files
            if vs_id not in kb_files_dict:
                kb_files_dict[vs_id] = {}

            # Update the file information with what we have
            for file in files:
                file_id = file["id"]
                # If we don't have this file in settings, add it with Unknown path
                # We'll keep existing paths if we have them
                if file_id not in kb_files_dict[vs_id]:
                    kb_files_dict[vs_id][file_id] = "Unknown (added to KB)"

            # Update settings and save
            settings.kb_files = kb_files_dict
            settings.save_to_file()

            # Update our local reference after saving
            vs_files = kb_files_dict.get(vs_id, {})

        # Add the files to the table
        for file in files:
            file_id = file["id"]
            file_path = vs_files.get(file_id, "Unknown path")
            file_status = file.get("status", "Available")
            table.add_row(file_id, file_path, file_status)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing files: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")


def _list_all_kbs(settings: Settings) -> None:
    """List all knowledge bases."""
    table = Table(title="Knowledge Bases:")
    table.add_column("Name", style="cyan")
    table.add_column("Vector Store ID", style="green")
    table.add_column("File Count", style="magenta")
    table.add_column("Default", style="yellow")

    # Add the KBs to the table
    for name, vs_id in settings.knowledge_bases.items():
        file_count = len(settings.kb_files.get(vs_id, {}))
        is_default = "(default)" if settings.default_kb == name else ""
        table.add_row(name, vs_id, str(file_count), is_default)

    console.print(table)


async def _list_kb_files(vs_id: str, settings: Settings) -> list[dict[str, Any]]:
    """List files in a knowledge base."""
    provider = await get_kb_provider(settings)
    files = await provider.list_files(vs_id)
    await provider.close()
    return files


@kb_app.command("rm", help="Remove a knowledge base")
def kb_rm(
    name: str,
    force: bool = typer.Option(False, "--force", "-f", help="Force removal without confirmation"),
    verbose: bool = verbose_option,
) -> None:
    """Remove a knowledge base."""
    if verbose:
        alleycat_logging.set_verbose(True)

    settings = Settings()

    # Check if the KB exists
    if name not in settings.knowledge_bases:
        console.print(f"[red]Knowledge base '{name}' does not exist[/red]")
        return

    # Get the vector store ID
    vs_id = settings.knowledge_bases[name]

    # Confirm removal
    if not force and not Confirm.ask(f"Are you sure you want to remove knowledge base '{name}'?"):
        console.print("Aborted")
        return

    try:
        # Remove the vector store
        result = asyncio.run(_delete_vector_store(vs_id, settings))

        if result:
            # Update settings - use dictionary operations
            kb_dict = dict(settings.knowledge_bases)
            kb_files_dict = dict(settings.kb_files)

            # Remove from dictionaries
            if name in kb_dict:
                del kb_dict[name]
                settings.knowledge_bases = kb_dict

            if vs_id in kb_files_dict:
                del kb_files_dict[vs_id]
                settings.kb_files = kb_files_dict

            # Clear default KB if it was this one
            if settings.default_kb == name:
                settings.default_kb = None

            # Save settings
            settings.save_to_file()

            console.print(f"[green]Removed knowledge base '{name}'[/green]")
        else:
            console.print(f"[red]Failed to remove knowledge base '{name}'[/red]")

    except Exception as e:
        console.print(f"[red]Error removing knowledge base: {e}[/red]")


async def _delete_vector_store(vs_id: str, settings: Settings) -> bool:
    """Delete a vector store."""
    provider = await get_kb_provider(settings)
    result = await provider.delete_vector_store(vs_id)
    await provider.close()
    return result


@kb_app.command("add", help="Add files to a knowledge base")
def kb_add(
    name: str,
    file_paths: list[str] = kb_add_file_paths_arg,
    verbose: bool = verbose_option,
) -> None:
    """Add files to a knowledge base."""
    if verbose:
        alleycat_logging.set_verbose(True)

    settings = Settings()

    # Debug output
    logging.debug(f"Loading settings from {settings.config_file}")
    logging.debug(f"Current knowledge bases: {settings.knowledge_bases}")

    # Check if the KB exists
    if name not in settings.knowledge_bases:
        console.print(f"[red]Knowledge base '{name}' does not exist[/red]")
        logging.debug(f"Available KBs: {list(dict(settings.knowledge_bases).keys())}")
        return

    # Get the vector store ID
    vs_id = settings.knowledge_bases[name]
    logging.debug(f"Using vector store ID: {vs_id}")

    # Convert file paths to Path objects and validate they exist
    paths: list[Path] = []
    for path_str in file_paths:
        path = Path(path_str)
        if not path.exists():
            console.print(f"[yellow]Warning: File '{path}' does not exist, skipping[/yellow]")
            continue
        paths.append(path)
        logging.debug(f"Adding file: {path}")

    if not paths:
        console.print("[red]No valid files provided[/red]")
        return

    # Confirm addition
    if not Confirm.ask(f"Add {len(paths)} files to knowledge base '{name}'?"):
        console.print("Aborted")
        return

    try:
        # Add the files to the vector store
        logging.debug(f"Adding {len(paths)} files to vector store {vs_id}")
        results = asyncio.run(_add_files_to_kb(vs_id, paths, settings))

        # Update settings with file paths - use dictionary operations
        kb_files_dict = dict(settings.kb_files)
        if vs_id not in kb_files_dict:
            kb_files_dict[vs_id] = {}

        logging.debug(f"Results from adding files: {results}")

        for result in results:
            file_id = result["file_id"]
            file_path = str(result["file_path"])
            kb_files_dict[vs_id][file_id] = file_path
            logging.debug(f"Added file ID {file_id} -> {file_path}")

        # Update the settings object with the modified dictionary
        settings.kb_files = kb_files_dict

        # Save settings
        logging.debug(f"Saving settings with updated kb_files: {settings.kb_files}")
        settings.save_to_file()

        console.print(f"[green]Added {len(results)} files to knowledge base '{name}'[/green]")

    except Exception as e:
        console.print(f"[red]Error adding files: {e}[/red]")
        import traceback

        console.print(f"[red]{traceback.format_exc()}[/red]")


async def _add_files_to_kb(vs_id: str, paths: list[Path], settings: Settings) -> list[dict[str, Any]]:
    """Add files to a knowledge base."""
    provider = await get_kb_provider(settings)
    results = await provider.add_files(vs_id, paths)
    await provider.close()
    return results


@kb_app.command("delete", help="Delete a file from a knowledge base")
def kb_delete_file(name: str, file_id: str, verbose: bool = verbose_option) -> None:
    """Delete a file from a knowledge base."""
    if verbose:
        alleycat_logging.set_verbose(True)

    settings = Settings()

    # Check if the KB exists
    if name not in settings.knowledge_bases:
        console.print(f"[red]Knowledge base '{name}' does not exist[/red]")
        return

    # Get the vector store ID
    vs_id = settings.knowledge_bases[name]

    # Check if the file exists in our records - use dictionary operations
    kb_files_dict = dict(settings.kb_files)

    try:
        # Delete the file from the vector store
        result = asyncio.run(_delete_file_from_kb(vs_id, file_id, settings))

        if result:
            # Update settings - use dictionary operations
            if vs_id in kb_files_dict and file_id in kb_files_dict[vs_id]:
                del kb_files_dict[vs_id][file_id]
                settings.kb_files = kb_files_dict

            # Save settings
            settings.save_to_file()

            console.print(f"[green]Removed file '{file_id}' from knowledge base '{name}'[/green]")
        else:
            console.print(f"[red]Failed to remove file '{file_id}' from knowledge base '{name}'[/red]")

    except Exception as e:
        console.print(f"[red]Error removing file: {e}[/red]")


async def _delete_file_from_kb(vs_id: str, file_id: str, settings: Settings) -> bool:
    """Delete a file from a knowledge base."""
    provider = await get_kb_provider(settings)
    result = await provider.delete_file(vs_id, file_id)
    await provider.close()
    return result


@kb_app.command("default", help="Set the default knowledge base")
def kb_set_default(name: str, verbose: bool = verbose_option) -> None:
    """Set the default knowledge base."""
    if verbose:
        alleycat_logging.set_verbose(True)

    settings = Settings()

    # Check if the KB exists
    if name not in settings.knowledge_bases:
        console.print(f"[red]Knowledge base '{name}' does not exist[/red]")
        return

    # Update settings
    settings.default_kb = name
    settings.save_to_file()

    console.print(f"[green]Set '{name}' as the default knowledge base[/green]")


@kb_app.command("clear-default", help="Clear the default knowledge base")
def kb_clear_default(verbose: bool = verbose_option) -> None:
    """Clear the default knowledge base."""
    if verbose:
        alleycat_logging.set_verbose(True)

    settings = Settings()

    # Check if there is a default KB
    if settings.default_kb is None:
        console.print("[yellow]No default knowledge base set[/yellow]")
        return

    # Update settings
    old_default = settings.default_kb
    settings.default_kb = None
    settings.save_to_file()

    console.print(f"[green]Cleared default knowledge base (was '{old_default}')[/green]")


if __name__ == "__main__":
    app()
