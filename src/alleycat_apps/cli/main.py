"""AlleyCat CLI application."""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from alleycat_core import logging
from alleycat_core.config.settings import Settings
from alleycat_core.llm import OpenAIFactory, Message

console = Console()
error_console = Console(stderr=True)

app = typer.Typer(
    name="alleycat",
    help="A command line tool for chat conversations with LLMs",
    add_completion=True
)

@app.command()
def chat(
    prompt: str = typer.Argument(
        ...,
        help="The prompt to send to the LLM"
    ),
    model: str = typer.Option(
        None,
        "--model", "-m",
        help="Model to use",
        envvar="ALLEYCAT_MODEL"
    ),
    temperature: Optional[float] = typer.Option(
        None,
        "--temperature", "-t",
        help="Sampling temperature",
        min=0.0,
        max=2.0,
    ),
    output_format: Optional[str] = typer.Option(
        None,
        "--format", "-f",
        help="Output format (text, markdown, json)",
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="OpenAI API key",
        envvar="ALLEYCAT_OPENAI_API_KEY"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose debug output"
    ),
) -> None:
    """Send a prompt to the LLM and get a response."""
    try:
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
            
        # Validate required settings
        if not settings.openai_api_key:
            logging.error(
                "OpenAI API key is required. "
                "Set it via ALLEYCAT_OPENAI_API_KEY environment variable "
                "or --api-key option."
            )
            sys.exit(1)
            
        # Create LLM provider
        factory = OpenAIFactory()
        llm = factory.create(
            api_key=settings.openai_api_key,
            model=settings.model,
            temperature=settings.temperature
        )
        
        # Send prompt and get response
        messages = [Message(role="user", content=prompt)]
        response = asyncio.run(llm.complete(messages))
        
        # Format and display response
        if settings.output_format == "markdown":
            logging.console.print(Markdown(response.content))
        elif settings.output_format == "json":
            logging.console.print_json(response.model_dump())
        else:
            logging.console.print(response.content)
            
        if verbose and response.usage:
            logging.info(
                f"Tokens used: [cyan]{response.usage.get('total_tokens', 'unknown')}[/cyan] "
                f"(prompt: {response.usage.get('prompt_tokens', 'unknown')}, "
                f"completion: {response.usage.get('completion_tokens', 'unknown')})"
            )
            
    except Exception as e:
        logging.error(str(e))
        if verbose:
            logging.error("Traceback:", style="bold")
            import traceback
            logging.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    app() 