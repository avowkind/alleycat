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
from typing import Any, NoReturn, TypeGuard

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
from alleycat_core.llm.types import ResponseFormat, ResponseFormatText
from alleycat_core.schema import SchemaManager, SchemaValidationError

console = Console()
error_console = Console(stderr=True)

app = typer.Typer(
    name="alleycat",
    help="A command line tool for chat conversations with LLMs",
    add_completion=True,
)

# Initialize schema manager
schema_manager = SchemaManager()


class OutputMode(str, enum.Enum):
    """Output mode options."""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    SCHEMA = "schema"  # New mode for schema-based output


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
no_stream_option = typer.Option(False, "--no-stream", help="Disable response streaming")
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
schema_option = typer.Option(
    None,
    "--schema",
    help="Path to JSON schema file for structured output",
)
schema_chain_option = typer.Option(
    None,
    "--schema-chain",
    help="Comma-separated paths to JSON schema files for chained processing",
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


def handle_non_stream_response(
    response: Any,
    console: Console,
    output_format: str = "text",
) -> None:
    """Handle a non-streaming response from the LLM.

    Args:
        response: The response from the LLM
        console: The console to print to
        output_format: The output format (text, markdown, json)

    """
    # Display the response - response ID is now tracked by the provider
    if output_format == "markdown":
        console.print(
            Markdown(
                response.output_text,
                code_theme="github-dark",
                hyperlinks=True,
                justify="left",
            )
        )
    elif output_format == "json":
        console.print_json(response.output_text)
    else:
        console.print(response.output_text)

    # Display token usage if verbose
    if logging.is_verbose() and response.usage:
        total = response.usage.total_tokens
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        logging.info(f"Tokens used: [cyan]{total}[/cyan] (prompt: {prompt_tokens}, completion: {completion_tokens})")


def handle_error_event(event: ResponseStreamEvent) -> NoReturn:
    """Handle error events from the LLM.

    Args:
        event: The error event to handle. Must be verified as an error event before calling.

    Raises:
        Exception: Always raises an exception with the appropriate error message

    """
    if not is_error_event(event):
        raise TypeError("Event must be an error event")

    error_msg = event.error.message
    if "context_length_exceeded" in error_msg or "maximum limit" in error_msg:
        logging.error("Error: The conversation has grown too large for the model's context window.")
        logging.error("Try starting a new conversation")
    elif "rate limit" in error_msg.lower():
        logging.error("Rate limit error: Too many requests in a short period.")
        logging.error("Please wait a moment before continuing.")
    else:
        logging.error(f"Error in stream: {error_msg}")
    raise Exception(error_msg)


def handle_stream_event(
    event: ResponseStreamEvent,
    accumulated_text: str,
    live: Live,
    output_format: str = "text",
) -> tuple[str, bool]:
    """Handle a single stream event and update the live display.

    Args:
        event: The stream event to handle
        accumulated_text: The current accumulated text
        live: The live display instance
        output_format: The output format (text or markdown)

    Returns:
        tuple[str, bool]: Updated accumulated text and whether to continue processing

    """
    if is_text_delta_event(event):
        accumulated_text += event.delta
        # Update the display based on format
        if output_format == "markdown":
            live.update(
                Markdown(
                    accumulated_text,
                    code_theme="github-dark",
                    hyperlinks=True,
                    justify="left",
                )
            )
        else:
            live.update(accumulated_text)
        return accumulated_text, True
    if event.type == "response.completed" and hasattr(event, "response"):
        # Response ID is now tracked by the provider
        return accumulated_text, True
    if is_error_event(event):
        handle_error_event(event)
    return accumulated_text, True


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
                    handle_error_event(event)
                # Ignore other event types for now
        except Exception as e:
            logging.error(f"Error during streaming: {str(e)}")
            raise
    else:
        # For text/markdown, we can stream in real-time
        try:
            with Live(console=logging.output_console, refresh_per_second=4) as live:
                async for event in stream:
                    accumulated_text, should_continue = handle_stream_event(
                        event,
                        accumulated_text,
                        live,
                        settings.output_format,
                    )
                    if not should_continue:
                        break
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
        stream=settings.stream,
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
    instructions: str | None = None,
) -> None:
    """Run the chat interaction with the LLM."""
    # Prepare response format based on settings
    response_format: ResponseFormat = None
    if settings.output_format == "json":
        response_format = ResponseFormatText(format="json")
    elif settings.output_format == "schema":
        # Schema should have been loaded and validated in chat()
        # and passed through in settings.response_format
        response_format = settings.response_format

    async with create_llm(settings) as llm:
        try:
            response = await llm.respond(
                input=prompt,
                text=response_format,
                instructions=instructions,
                web_search=settings.enable_web_search,
                vector_store_id=settings.vector_store_id,
                tools_requested=getattr(settings, "tools_requested", ""),
            )

            match response:
                case AsyncIterator():
                    await handle_stream(response, settings)
                case _:
                    handle_non_stream_response(response, console, settings.output_format)

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
    instructions: str | None = None,
) -> None:
    """Run interactive chat mode with continuous conversation."""
    # Display opening banner
    console.print("[bold]Alleycat Interactive Chat[/bold]")

    async with create_llm(settings) as llm:
        # Prepare response format based on settings
        response_format: ResponseFormat = None
        if settings.output_format == "json":
            response_format = ResponseFormatText(format="json")

        # Initial prompt from the user
        current_prompt = initial_prompt

        try:
            while True:
                response = await llm.respond(
                    input=current_prompt,
                    text=response_format,
                    instructions=instructions,
                    web_search=settings.enable_web_search,
                    vector_store_id=settings.vector_store_id,
                    tools_requested=getattr(settings, "tools_requested", ""),
                )

                # Handle the response based on its type
                match response:
                    case AsyncIterator():
                        # For streaming, we need to accumulate the response as we display it
                        accumulated_text = ""
                        with Live(console=console, refresh_per_second=4) as live:
                            async for event in response:
                                accumulated_text, should_continue = handle_stream_event(
                                    event,
                                    accumulated_text,
                                    live,
                                    settings.output_format,
                                )
                                if not should_continue:
                                    break
                    case _:
                        handle_non_stream_response(response, console, settings.output_format)

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
    no_stream: bool = no_stream_option,
    chat_mode: bool = chat_option,
    instructions: str = instructions_option,
    file: str = file_option,
    tools: str = tool_option,
    web: bool = web_option,
    setup: bool = setup_option,
    remove_config: bool = remove_config_option,
    kb: list[str] = kb_option,
    schema: str = schema_option,
    schema_chain: str = schema_chain_option,
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
        no_stream: Disable response streaming
        chat_mode: Interactive chat mode with continuous conversation
        instructions: System instructions for the model
        file: Path to a file to use in the conversation
        tools: Enabled tools (web, file-search)
        web: Enable web search (alias for --tool web)
        setup: Run the setup wizard to configure AlleyCat
        remove_config: Remove AlleyCat configuration and data files
        kb: Knowledge base name to use for search (can be repeated)
        schema: Path to JSON schema file for structured output
        schema_chain: Comma-separated paths to JSON schema files for chained processing

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

        # Handle schema options first to ensure proper streaming behavior
        if schema:
            try:
                # Validate and load the schema
                schema_obj = schema_manager.get_schema(schema)
                settings.output_format = "schema"
                # Store the response format directly in settings
                settings.response_format = schema_obj.to_request_format()
                # Disable streaming for schema output
                settings.stream = False
                if stream:
                    logging.info("Streaming disabled for schema output format")
            except SchemaValidationError as e:
                logging.error(f"Schema validation error: {e}")
                sys.exit(1)
            except Exception as e:
                logging.error(f"Error loading schema: {e}")
                sys.exit(1)
        elif schema_chain:
            try:
                # Load and validate each schema in the chain
                schema_paths = [Path(s.strip()) for s in schema_chain.split(",")]
                for schema_path in schema_paths:
                    schema_manager.validate_schema_file(schema_path)
                settings.schema_chain = schema_paths
                settings.output_format = "schema"
                # Disable streaming for schema chain
                settings.stream = False
                if stream:
                    logging.info("Streaming disabled for schema chain output format")
                # TODO: Implement schema chain response format
            except SchemaValidationError as e:
                logging.error(f"Schema validation error: {e}")
                sys.exit(1)
            except Exception as e:
                logging.error(f"Error loading schema chain: {e}")
                sys.exit(1)

        # Override settings with any provided arguments
        if api_key:
            settings.openai_api_key = api_key
        if model:
            settings.model = model
        if temperature is not None:
            settings.temperature = temperature
        if output_mode:
            settings.output_format = output_mode.value  # Use the value from the enum
            # Disable streaming for JSON output
            if settings.output_format == "json":
                settings.stream = False
                if stream:
                    logging.info("Streaming disabled for JSON output format")

        # Enable streaming by default in chat mode, unless using incompatible output format
        if chat_mode and settings.output_format not in ("json", "schema"):
            settings.stream = not no_stream  # Use no_stream flag to override default
            if settings.stream and not stream:
                logging.info("Streaming enabled by default in chat mode")
            elif no_stream:
                logging.info("Streaming explicitly disabled in chat mode")
        elif stream and settings.output_format not in ("json", "schema"):
            settings.stream = stream

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
        if kb or settings.default_kb:
            if logging.is_verbose():
                logging.info(f"Processing knowledge base request: {kb}")
                logging.info(
                    f"Current state - tools_requested: {settings.tools_requested}, default_kb: {settings.default_kb}"
                )

            # Always set tools_requested to include file_search when using KB
            if not settings.tools_requested:
                settings.tools_requested = "file_search"
            elif "file_search" not in settings.tools_requested and "file-search" not in settings.tools_requested:
                settings.tools_requested += ",file_search"

            # Use provided KB list or default KB
            kb_list: list[str] = []
            if kb:
                kb_list = kb
            elif settings.default_kb and isinstance(settings.default_kb, str):
                kb_list = [settings.default_kb]

            # Find the vector store IDs from the knowledge base names
            vector_store_ids = []
            for kb_name in kb_list:
                if kb_name in settings.knowledge_bases:
                    vector_store_id = settings.knowledge_bases[kb_name]
                    vector_store_ids.append(vector_store_id)
                    if logging.is_verbose():
                        logging.info(f"Found vector store ID for '{kb_name}': {vector_store_id}")
                else:
                    logging.warning(
                        f"Knowledge base '{kb_name}' not found in configuration. Available: {list(settings.knowledge_bases.keys())}"
                    )

            # Set the vector store ID to the comma-separated list of vector store IDs
            if vector_store_ids:
                settings.vector_store_id = ",".join(vector_store_ids)
            elif not settings.vector_store_id and settings.default_kb:
                # Try to use default KB's vector store ID
                if settings.default_kb in settings.knowledge_bases:
                    settings.vector_store_id = settings.knowledge_bases[settings.default_kb]
                else:
                    logging.warning("Default knowledge base not found in configuration.")

            if logging.is_verbose():
                logging.info(
                    f"Final state - tools_requested: {settings.tools_requested}, vector_store_id: {settings.vector_store_id}"
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

        # For debug: Log the settings
        if verbose:
            logging.info(
                f"Final settings: enable_web_search={settings.enable_web_search}, "
                f"vector_store_id={settings.vector_store_id}, "
                f"tools_requested={settings.tools_requested}"
            )

        # Run in interactive chat mode if --chat is specified
        if chat_mode:
            try:
                asyncio.run(run_interactive_chat(prompt, settings, instruction_text))
            except KeyboardInterrupt:
                logging.info("Chat session ended by user.")
                sys.exit(0)
        else:
            # Run the normal chat interaction
            asyncio.run(run_chat(prompt, settings, instruction_text))

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
