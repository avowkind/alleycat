"""AlleyCat CLI application."""

import asyncio
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import typer
from openai.types.responses.response_stream_event import ResponseStreamEvent
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from alleycat_core import logging
from alleycat_core.config.settings import Settings
from alleycat_core.llm import OpenAIFactory

console = Console()
error_console = Console(stderr=True)

app = typer.Typer(
    name="alleycat",
    help="A command line tool for chat conversations with LLMs",
    add_completion=True,
)


def get_prompt_from_stdin() -> str:
    """Read prompt from stdin if available."""
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


async def handle_stream(
    stream: AsyncIterator[ResponseStreamEvent], settings: Settings
) -> None:
    """Handle streaming response from the LLM."""
    accumulated_text = ""

    if settings.output_format == "json":
        # For JSON, we need to accumulate the entire response
        try:
            async for event in stream:
                match event.type:
                    case "response.output_text.delta":
                        accumulated_text += event.delta
                    case "response.completed":
                        # Final text received, format and output
                        logging.output_console.print_json(accumulated_text)
                    case "error":
                        logging.error(f"Error in stream: {event.error.message}")
                        raise Exception(event.error.message)
                    case "response.failed":
                        logging.error(f"Stream failed: {event.error.message}")
                        raise Exception(event.error.message)
                    case _:
                        # Ignore other event types for now
                        pass
        except Exception as e:
            logging.error(f"Error during streaming: {str(e)}")
            raise
    else:
        # For text/markdown, we can stream in real-time
        try:
            with Live(console=logging.output_console, refresh_per_second=4) as live:
                async for event in stream:
                    match event.type:
                        case "response.output_text.delta":
                            accumulated_text += event.delta
                            if settings.output_format == "markdown":
                                live.update(Markdown(accumulated_text))
                            else:
                                live.update(accumulated_text)
                        case "error":
                            logging.error(f"Error in stream: {event.error.message}")
                            raise Exception(event.error.message)
                        case "response.failed":
                            logging.error(f"Stream failed: {event.error.message}")
                            raise Exception(event.error.message)
                        case _:
                            # Ignore other event types for now
                            pass
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


async def run_chat(
    prompt: str,
    settings: Settings,
    stream: bool = False,
    instructions: str | None = None,
) -> None:
    """Run the chat interaction with the LLM."""
    # Create LLM provider
    factory = OpenAIFactory()
    llm = factory.create(
        api_key=settings.openai_api_key,
        model=settings.model,
        temperature=settings.temperature,
    )

    try:
        if stream:
            # Use the respond method with streaming
            response_stream = await llm.respond(
                input=prompt,
                stream=True,
                text=(
                    {"format": settings.output_format}
                    if settings.output_format == "json"
                    else None
                ),
                instructions=instructions,
            )
            await handle_stream(response_stream, settings)
        else:
            # Use the respond method without streaming
            response = await llm.respond(
                input=prompt,
                text=(
                    {"format": settings.output_format}
                    if settings.output_format == "json"
                    else None
                ),
                instructions=instructions,
            )

            # Get response text, handling both string and structured responses
            response_text = response.output_text

            # Format and display response
            if settings.output_format == "markdown":
                logging.output(Markdown(response_text))
            elif settings.output_format == "json":
                logging.output_console.print_json(response_text)
            else:
                logging.output(response_text)

            if logging.is_verbose() and response.usage:
                total = getattr(response.usage, "total_tokens", "unknown")
                prompt_tokens = getattr(response.usage, "prompt_tokens", "unknown")
                completion_tokens = getattr(
                    response.usage, "completion_tokens", "unknown"
                )
                logging.info(
                    f"Tokens used: [cyan]{total}[/cyan] "
                    f"(prompt: {prompt_tokens}, "
                    f"completion: {completion_tokens})"
                )
    except Exception as e:
        logging.error(str(e))
        if logging.is_verbose():
            logging.error("Traceback:", style="bold")
            import traceback

            logging.error(traceback.format_exc())
        raise


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def chat(
    ctx: typer.Context,
    model: str = typer.Option(
        None, "--model", "-m", help="Model to use", envvar="ALLEYCAT_MODEL"
    ),
    temperature: float | None = typer.Option(
        None,
        "--temperature",
        "-t",
        help="Sampling temperature",
        min=0.0,
        max=2.0,
    ),
    output_format: str | None = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format (text, markdown, json)",
    ),
    api_key: str | None = typer.Option(
        None, "--api-key", help="OpenAI API key", envvar="ALLEYCAT_OPENAI_API_KEY"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose debug output"
    ),
    stream: bool = typer.Option(
        False, "--stream", "-s", help="Stream the response as it's generated"
    ),
    instructions: str = typer.Option(
        None,
        "--instructions",
        "-i",
        help="System instructions (either a string or path to a file)",
    ),
) -> None:
    """Send a prompt to the LLM and get a response.

    The prompt can be provided in two ways:
    1. As command line arguments: alleycat tell me a joke
    2. Via stdin: echo "tell me a joke" | alleycat

    System instructions can be provided either directly or from a file:
    1. Direct: alleycat -i "You are a helpful assistant" "tell me a joke"
    2. From file: alleycat -i prompts/assistant.txt "tell me a joke"
    """
    try:
        # Set verbosity level
        logging.set_verbose(verbose)

        # Get prompt from command line args or stdin
        prompt = " ".join(ctx.args) if ctx.args else get_prompt_from_stdin()

        if not prompt:
            logging.error(
                "No prompt provided. Either pass it as arguments or via stdin:\n"
                "  alleycat tell me a joke\n"
                "  echo 'tell me a joke' | alleycat"
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
        if output_format is not None:
            settings.output_format = output_format

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

        # Run the chat interaction in a new event loop
        asyncio.run(run_chat(prompt, settings, stream, instruction_text))

    except Exception as e:
        logging.error(str(e))
        if verbose:
            logging.error("Traceback:", style="bold")
            import traceback

            logging.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    app()
