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
) -> None:
    """Send a prompt to the LLM and get a response.

    The prompt can be provided in two ways:
    1. As command line arguments: alleycat tell me a joke
    2. Via stdin: echo "tell me a joke" | alleycat

    System instructions can be provided either directly or from a file:
    1. Direct: alleycat -i "You are a helpful assistant" "tell me a joke"
    2. From file: alleycat -i prompts/assistant.txt "tell me a joke"

    For interactive chat mode with continuous conversation:
    alleycat --chat "Hello, how are you today?"
    Or start a chat without an initial prompt:
    alleycat --chat

    To include a file for the model to analyze:
    alleycat -f path/to/file.pdf "Analyze this file"
    Text files (.txt, .log, .md, .csv) will be included directly in the prompt.
    Binary files (.pdf, .json) will be uploaded to OpenAI.

    To change the output mode:
    alleycat -m markdown "Tell me a joke"
    """
    try:
        # Set verbosity level
        logging.set_verbose(verbose)

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

        # Load base settings from environment
        settings = Settings()

        # Override with command line options if provided
        if api_key is not None:
            settings.openai_api_key = api_key
        if model is not None:
            settings.model = model
        if temperature is not None:
            settings.temperature = temperature
        if output_mode is not None:
            settings.output_format = output_mode.value  # Use the value from the enum
        if file is not None:
            settings.file_path = file

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
    app()
