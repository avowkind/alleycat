"""AlleyCat CLI application.

This module contains the CLI application for AlleyCat.

It uses the `typer` library to define the CLI and the
`openai.types.responses.response_stream_event.ResponseStreamEvent`
to define the types for the OpenAI API.

Author: Andrew Watkins <andrew@groat.nz>
"""

import asyncio
import enum
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, TypeGuard

import typer
from openai.types.responses.response_stream_event import ResponseStreamEvent
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt

from alleycat_apps.cli.admin_cmd import app as admin_app
from alleycat_core import logging
from alleycat_core.config.settings import Settings
from alleycat_core.llm import OpenAIFactory
from alleycat_core.llm.types import ResponseFormat

console = Console()
error_console = Console(stderr=True)

app = typer.Typer(
    name="alleycat",
    help="A command line tool for chat conversations with LLMs",
    add_completion=True,
)


class OutputMode(str, enum.Enum):
    """Output mode options."""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"


# Define command options at module level
model_option = typer.Option(None, "--model", help="Model to use", envvar="ALLEYCAT_MODEL")
temperature_option = typer.Option(
    None,
    "--temperature",
    "-t",
    help="Sampling temperature",
    min=0.0,
    max=2.0,
)
mode_option = typer.Option(
    None,
    "--mode",
    "-m",
    help="Output mode (text, markdown, json)",
)
api_key_option = typer.Option(None, "--api-key", help="OpenAI API key", envvar="ALLEYCAT_OPENAI_API_KEY")
verbose_option = typer.Option(False, "--verbose", "-v", help="Enable verbose debug output")
stream_option = typer.Option(False, "--stream", "-s", help="Stream the response as it's generated")
chat_option = typer.Option(False, "--chat", "-c", help="Interactive chat mode with continuous conversation")
instructions_option = typer.Option(
    None,
    "--instructions",
    "-i",
    help="System instructions (either a string or path to a file)",
)
file_option = typer.Option(
    None,
    "--file",
    "-f",
    help="Path to a file to upload and reference in the conversation",
)
tool_option = typer.Option(
    None,
    "--tool",
    "-t",
    help="Enable specific tools (web, file-search)",
)
web_option = typer.Option(
    False,
    "--web",
    "-w",
    help="Enable web search (alias for --tool web)",
)
# Define KB option separately to avoid typing issues
kb_help = "Knowledge base name to use for search (can be repeated)"
kb_option = typer.Option(
    None,
    "--kb",
    help=kb_help,
)
setup_option = typer.Option(
    False,
    "--setup",
    help="Run the setup wizard to configure AlleyCat",
)
remove_config_option = typer.Option(
    False,
    "--remove-config",
    help="Remove AlleyCat configuration and data files",
)


def get_prompt_from_stdin() -> str:
    """Read prompt from stdin if available."""
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def is_text_delta_event(event: ResponseStreamEvent) -> TypeGuard[Any]:
    """Check if event is a text delta event."""
    return event.type == "response.output_text.delta" and hasattr(event, "delta")


def is_error_event(event: ResponseStreamEvent) -> TypeGuard[Any]:
    """Check if event is an error event."""
    return event.type in ("error", "response.failed") and hasattr(event, "error") and hasattr(event.error, "message")


async def handle_stream(stream: AsyncIterator[ResponseStreamEvent], settings: Settings) -> None:
    """Handle streaming response from the LLM."""
    accumulated_text = ""

    if settings.output_format == "json":
        # For JSON, we need to accumulate the entire response
        try:
            async for event in stream:
                if is_text_delta_event(event):
                    accumulated_text += event.delta
                elif event.type == "response.completed":
                    # Final text received, format and output
                    logging.output_console.print_json(accumulated_text)
                elif is_error_event(event):
                    error_msg = event.error.message
                    if "context_length_exceeded" in error_msg or "maximum limit" in error_msg:
                        logging.error("Error: The conversation has grown too large for the model's context window.")
                        logging.error("Try starting a new conversation or using a model with a larger context window.")
                    elif "rate limit" in error_msg.lower():
                        logging.error("Rate limit error: Too many requests in a short period.")
                        logging.error("Please wait a moment before continuing.")
                    else:
                        logging.error(f"Error in stream: {error_msg}")
                    raise Exception(error_msg)
                # Ignore other event types for now
        except Exception as e:
            logging.error(f"Error during streaming: {str(e)}")
            raise
    else:
        # For text/markdown, we can stream in real-time
        try:
            with Live(console=logging.output_console, refresh_per_second=4) as live:
                async for event in stream:
                    if is_text_delta_event(event):
                        accumulated_text += event.delta
                        if settings.output_format == "markdown":
                            live.update(Markdown(accumulated_text))
                        else:
                            live.update(accumulated_text)
                    elif is_error_event(event):
                        error_msg = event.error.message
                        if "context_length_exceeded" in error_msg or "maximum limit" in error_msg:
                            logging.error("Error: The conversation has grown too large for the model's context window.")
                            logging.error(
                                "Try starting a new conversation or using a model with a larger context window."
                            )
                        elif "rate limit" in error_msg.lower():
                            logging.error("Rate limit error: Too many requests in a short period.")
                            logging.error("Please wait a moment before continuing.")
                        else:
                            logging.error(f"Error in stream: {error_msg}")
                        raise Exception(error_msg)
                    # Ignore other event types for now
        except Exception as e:
            logging.error(f"Error during streaming: {str(e)}")
            raise


def read_instructions_file(filepath: str) -> str:
    """Read instructions from a file."""
    try:
        path = Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"Instructions file not found: {filepath}")
        return path.read_text().strip()
    except Exception as e:
        logging.error(f"Error reading instructions file: {e}")
        sys.exit(1)


@asynccontextmanager
async def create_llm(settings: Settings) -> AsyncIterator[Any]:
    """Create an LLM instance as a context manager."""
    factory = OpenAIFactory()
    llm = factory.create(
        api_key=settings.openai_api_key,
        model=settings.model,
        temperature=settings.temperature,
    )

    try:
        # Setup file if specified
        if settings.file_path:
            success = await llm.add_file(settings.file_path)
            if not success:
                raise ValueError(f"Failed to setup file: {settings.file_path}")

            if logging.is_verbose():
                logging.info(f"Successfully setup file: {settings.file_path}")

        yield llm
    finally:
        await llm.close()


async def run_chat(
    prompt: str,
    settings: Settings,
    stream: bool = False,
    instructions: str | None = None,
) -> None:
    """Run the chat interaction with the LLM."""
    # Prepare response format based on settings
    response_format: ResponseFormat = None
    if settings.output_format == "json":
        response_format = {"format": "json"}

    async with create_llm(settings) as llm:
        try:
            if stream:
                # Use the respond method with streaming
                response_stream = await llm.respond(
                    input=prompt,
                    stream=True,
                    text=response_format,
                    instructions=instructions,
                    web_search=settings.enable_web_search,
                    vector_store_id=settings.vector_store_id,
                    tools_requested=getattr(settings, "tools_requested", ""),
                )
                # Since the respond method can return either a stream or a regular response,
                # we need to ensure we have a stream here
                if isinstance(response_stream, AsyncIterator):
                    await handle_stream(response_stream, settings)
                else:
                    # This should never happen with stream=True
                    raise TypeError("Expected streaming response but got non-streaming response")
            else:
                # Use the respond method without streaming
                response = await llm.respond(
                    input=prompt,
                    text=response_format,
                    instructions=instructions,
                    web_search=settings.enable_web_search,
                    vector_store_id=settings.vector_store_id,
                    tools_requested=getattr(settings, "tools_requested", ""),
                )

                # Since the respond method can return either a stream or a regular response,
                # we need to ensure we have a regular response here
                if not isinstance(response, AsyncIterator):
                    # Get response text from the LLMResponse object
                    response_text = response.output_text

                    # Format and display response
                    if settings.output_format == "markdown":
                        logging.output(Markdown(response_text))
                    elif settings.output_format == "json":
                        logging.output_console.print_json(response_text)
                    else:
                        logging.output(response_text)

                    if logging.is_verbose() and response.usage:
                        total = response.usage.total_tokens
                        prompt_tokens = response.usage.prompt_tokens
                        completion_tokens = response.usage.completion_tokens
                        logging.info(
                            f"Tokens used: [cyan]{total}[/cyan] "
                            f"(prompt: {prompt_tokens}, completion: {completion_tokens})"
                        )
                else:
                    # This should never happen with stream=False
                    raise TypeError("Expected non-streaming response but got streaming response")
        except Exception as e:
            logging.error(str(e))
            if logging.is_verbose():
                logging.error("Traceback:", style="bold")
                import traceback

                logging.error(traceback.format_exc())
            raise


async def run_interactive_chat(
    initial_prompt: str,
    settings: Settings,
    stream: bool = False,
    instructions: str | None = None,
) -> None:
    """Run interactive chat mode with continuous conversation."""
    # Display opening banner
    console.print("[bold]Alleycat Interactive Chat[/bold]")

    async with create_llm(settings) as llm:
        # Prepare response format based on settings
        response_format: ResponseFormat = None
        if settings.output_format == "json":
            response_format = {"format": "json"}

        # Initial prompt from the user
        current_prompt = initial_prompt

        try:
            while True:
                # Get response from LLM - no need to manage previous_response_id
                # as it's now handled in the provider
                response = await llm.respond(
                    input=current_prompt,
                    text=response_format,
                    instructions=instructions,
                    stream=stream,
                    web_search=settings.enable_web_search,
                    vector_store_id=settings.vector_store_id,
                    tools_requested=getattr(settings, "tools_requested", ""),
                )

                # Handle the response
                if stream:
                    if isinstance(response, AsyncIterator):
                        # For streaming, we need to accumulate the response as we display it
                        accumulated_text = ""
                        async for event in response:
                            if is_text_delta_event(event):
                                accumulated_text += event.delta
                                # Update the display - we'll use the same approach as handle_stream
                                if settings.output_format == "markdown":
                                    console.print(Markdown(event.delta), end="")
                                else:
                                    console.print(event.delta, end="")
                            elif event.type == "response.completed" and hasattr(event, "response"):
                                # Response ID is now tracked by the provider
                                console.print("\n")  # Add a newline at the end
                            elif is_error_event(event):
                                error_msg = event.error.message
                                if "context_length_exceeded" in error_msg or "maximum limit" in error_msg:
                                    logging.error(
                                        "Error: The conversation has grown too large for the model's context window."
                                    )
                                    logging.error(
                                        "Try starting a new conversation or using a model with a larger context window."
                                    )
                                elif "rate limit" in error_msg.lower():
                                    logging.error("Rate limit error: Too many requests in a short period.")
                                    logging.error("Please wait a moment before continuing.")
                                else:
                                    logging.error(f"Error in stream: {error_msg}")
                                raise Exception(error_msg)
                    else:
                        raise TypeError("Expected streaming response but got non-streaming response")
                else:
                    # Non-streaming response
                    if not isinstance(response, AsyncIterator):
                        # Display the response - response ID is now tracked by the provider
                        if settings.output_format == "markdown":
                            console.print(Markdown(response.output_text))
                        elif settings.output_format == "json":
                            console.print_json(response.output_text)
                        else:
                            console.print(response.output_text)

                        # Display token usage if verbose
                        if logging.is_verbose() and response.usage:
                            total = response.usage.total_tokens
                            prompt_tokens = response.usage.prompt_tokens
                            completion_tokens = response.usage.completion_tokens
                            logging.info(
                                f"Tokens used: [cyan]{total}[/cyan] "
                                f"(prompt: {prompt_tokens}, completion: {completion_tokens})"
                            )
                    else:
                        raise TypeError("Expected non-streaming response but got streaming response")

                # Get the next prompt from the user
                console.print("")
                try:
                    current_prompt = Prompt.ask("[bold cyan]>[/bold cyan]")
                    if not current_prompt.strip():
                        # If user entered empty input, exit
                        break
                except KeyboardInterrupt:
                    console.print("\nExiting chat...")
                    break

        except Exception as e:
            logging.error(str(e))
            if logging.is_verbose():
                logging.error("Traceback:", style="bold")
                import traceback

                logging.error(traceback.format_exc())
            raise


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def chat(
    ctx: typer.Context,
    model: str = model_option,
    temperature: float | None = temperature_option,
    output_mode: OutputMode | None = mode_option,
    api_key: str | None = api_key_option,
    verbose: bool = verbose_option,
    stream: bool = stream_option,
    chat_mode: bool = chat_option,
    instructions: str = instructions_option,
    file: str = file_option,
    tools: str = tool_option,
    web: bool = web_option,
    setup: bool = setup_option,
    remove_config: bool = remove_config_option,
    kb: list[str] = kb_option,
) -> None:
    """Send a prompt to the LLM and get a response.

    Args:
        ctx: Typer context
        model: Model to use (overrides config)
        temperature: Sampling temperature (overrides config)
        output_mode: Output mode (text, markdown, json)
        api_key: OpenAI API key (overrides config)
        verbose: Enable verbose debug output
        stream: Stream the response as it's generated
        chat_mode: Interactive chat mode with continuous conversation
        instructions: System instructions for the model
        file: Path to a file to use in the conversation
        tools: Enabled tools (web, file-search)
        web: Enable web search (alias for --tool web)
        setup: Run the setup wizard to configure AlleyCat
        remove_config: Remove AlleyCat configuration and data files
        kb: Knowledge base name to use for search (can be repeated)

    """
    try:
        # Configure logging
        if verbose:
            logging.set_verbose(True)

        # Check if setup was requested
        if setup:
            # Run the setup wizard
            admin_app(["setup"])
            return

        # Check if config removal was requested
        if remove_config:
            # Run the setup wizard with remove flag
            admin_app(["setup", "--remove"])
            return

        # Get prompt from command line args or stdin
        prompt = " ".join(ctx.args) if ctx.args else get_prompt_from_stdin()

        # Check if prompt is required
        if not prompt:
            if chat_mode:
                # In chat mode, use a default greeting if no prompt is provided
                prompt = "Hello! I'm ready to chat."
                logging.info("Starting chat with default greeting.")
            else:
                # In normal mode, require a prompt
                logging.error(
                    "No prompt provided. Either pass it as arguments or via stdin:\n"
                    "  alleycat tell me a joke\n"
                    "  echo 'tell me a joke' | alleycat\n"
                    "Or use --chat to start an interactive session without an initial prompt."
                )
                sys.exit(1)

        # Create settings with priority order:
        # 1. Default values (lowest priority)
        settings = Settings()

        # 2. Load from config file
        settings.load_from_file()

        # 3. Environment variables (handled by pydantic)

        # 4. Command-line arguments (highest priority)
        # Override settings with any provided arguments
        if api_key:
            settings.openai_api_key = api_key
        if model:
            settings.model = model
        if temperature is not None:
            settings.temperature = temperature
        if output_mode:
            settings.output_format = output_mode.value  # Use the value from the enum

        # For debug: log all environment variable values
        if verbose:
            logging.info(f"Settings loaded vector_store_id = {settings.vector_store_id}")

        # Set file path
        if file is not None:
            settings.file_path = file

        # Process tools
        if tools:
            tool_values = tools.split(",")
            settings.tools_requested = tools  # Store the raw tools string
            for tool in tool_values:
                tool = tool.strip().lower()
                if tool == "web":
                    settings.enable_web_search = True
                elif tool == "file-search":
                    # Always update the tools_requested to include file_search
                    if "file-search" in settings.tools_requested and "file_search" not in settings.tools_requested:
                        settings.tools_requested = settings.tools_requested.replace("file-search", "file_search")

        # Handle --web option as an alias for --tool web
        if web:
            settings.enable_web_search = True
            if not settings.tools_requested:
                settings.tools_requested = "web"
            elif "web" not in settings.tools_requested:
                settings.tools_requested += ",web"

        # Handle the knowledge base options
        if kb:
            # Make sure tools_requested has file_search
            if not settings.tools_requested:
                settings.tools_requested = "file_search"
            elif "file_search" not in settings.tools_requested and "file-search" not in settings.tools_requested:
                settings.tools_requested += ",file_search"

            # Find the vector store IDs from the knowledge base names
            vector_store_ids = []
            for kb_name in kb:
                if kb_name in settings.knowledge_bases:
                    vector_store_ids.append(settings.knowledge_bases[kb_name])
                    if logging.is_verbose():
                        logging.info(
                            f"Using knowledge base '{kb_name}'"
                            f" with vector store ID: {settings.knowledge_bases[kb_name]}"
                        )
                else:
                    logging.warning(f"Knowledge base '{kb_name}' not found in configuration. Skipping.")

            # Set the vector store ID to the comma-separated list of vector store IDs
            if vector_store_ids:
                settings.vector_store_id = ",".join(vector_store_ids)
                if logging.is_verbose():
                    logging.info(f"Using vector store IDs: {settings.vector_store_id}")
            elif not settings.vector_store_id:
                # No vector store ID found
                logging.warning("No valid knowledge bases found. File search may not work correctly.")

        # For debug: Log the settings
        if verbose:
            logging.info(
                f"Final settings: enable_web_search={settings.enable_web_search}, "
                f"vector_store_id={settings.vector_store_id}, "
                f"tools_requested={settings.tools_requested}"
            )

        # Handle instructions
        instruction_text = None
        if instructions:
            # Check if instructions is a file path
            if Path(instructions).exists():
                instruction_text = read_instructions_file(instructions)
            else:
                instruction_text = instructions

        # Validate required settings
        if not settings.openai_api_key:
            # No API key found, check if config file exists
            if settings.config_file is None or not settings.config_file.exists():
                # No config file and no API key, run initialization wizard automatically
                console.print("[yellow]No configuration or API key found. Running initialization wizard...[/yellow]")
                admin_app(["setup"])

                # After init, reload settings
                settings = Settings()
                settings.load_from_file()

                # If we still don't have an API key, exit with error
                if not settings.openai_api_key:
                    logging.error("OpenAI API key is still not configured. Exiting.")
                    sys.exit(1)
            else:
                # Config file exists but no API key, display normal error
                logging.error(
                    "OpenAI API key is required. "
                    "Set it via ALLEYCAT_OPENAI_API_KEY environment variable "
                    "or --api-key option."
                )
                sys.exit(1)

        # Run in interactive chat mode if --chat is specified
        if chat_mode:
            try:
                asyncio.run(run_interactive_chat(prompt, settings, stream, instruction_text))
            except KeyboardInterrupt:
                logging.info("Chat session ended by user.")
                sys.exit(0)
        else:
            # Run the normal chat interaction
            asyncio.run(run_chat(prompt, settings, stream, instruction_text))

    except ValueError as e:
        # This could be due to file setup issues
        logging.error(str(e))
        sys.exit(1)
    except FileNotFoundError as e:
        # File not found
        logging.error(str(e))
        logging.error("Please check the file path and try again.")
        sys.exit(1)
    except Exception as e:
        logging.error(str(e))
        if verbose:
            logging.error("Traceback:", style="bold")
            import traceback

            logging.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # Run the Typer app directly - all command line args are handled by chat
    app()
