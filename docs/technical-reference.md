# Alleycat Technical Reference

This document provides a detailed technical overview of the Alleycat system architecture, including its package structure, core abstractions, and key components.

## Package Structure

The codebase follows a clean architecture pattern with clear separation of concerns:

```
alleycat/
├── src/
│   ├── alleycat_apps/      # Application layer
│   │   └── cli/           # Command-line interface
│   └── alleycat_core/     # Core business logic
│       ├── config/        # Configuration management
│       ├── llm/          # LLM provider implementations
│       └── logging/       # Logging utilities
├── tests/                 # Test files
├── pyproject.toml         # Project configuration
└── setup.py              # Development installation
```

### Core Package (`alleycat_core`)

The core package contains the business logic and domain models, independent of any delivery mechanism:

1. **LLM Interface Layer** (`llm/`)
   - `base.py`: Abstract base classes for LLM interfaces
   - `openai.py`: OpenAI implementation
   - `types.py`: Common type definitions
   - `remote_file.py`: File handling abstractions

2. **Configuration** (`config/`)
   - `settings.py`: Application settings using Pydantic
   - Environment variable and .env file support
   - XDG Base Directory specification for config file locations
   - YAML-based configuration persistence

3. **Logging** (`logging.py`)
   - Rich console output formatting
   - Themed logging levels
   - Structured output handling

### Applications (`alleycat_apps`)

The applications package contains delivery mechanisms and user interfaces:

1. **Command Line Interface** (`cli/`)
   - `main.py`: Entry point and command handling
   - `init_cmd.py`: Configuration initialization and cleanup
   - Single-shot and interactive modes
   - File handling integration
   - Output formatting options

## Core Abstractions

### LLM Provider Interface

The system uses a clean abstraction for LLM providers through the `LLMProvider` abstract base class:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def respond(
        self,
        input: str | ResponseInputParam,
        *,
        stream: bool = False,
        instructions: str | None = None,
        text: ResponseFormat = None,
        **kwargs: Any,
    ) -> LLMResponse | AsyncIterator[ResponseStreamEvent]:
        """Send a request to the LLM."""
        pass

    @abstractmethod
    async def complete(self, messages: list[Message], **kwargs: Any) -> LLMResponse:
        """Send a completion request to the LLM."""
        pass

    @abstractmethod
    async def add_file(self, file_path: str) -> bool:
        """Add a file for use with the LLM."""
        pass
```

This abstraction allows:

- Multiple provider implementations (currently OpenAI, extensible to others)
- Streaming and non-streaming responses
- File handling capabilities
- Custom instructions and formatting

### File Handling

File handling is abstracted through the `RemoteFile` interface:

```python
class RemoteFile(ABC):
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the remote file, uploading if necessary."""
        pass

    @abstractmethod
    async def cleanup(self) -> bool:
        """Clean up the remote file, deleting if necessary."""
        pass

    @abstractmethod
    def get_file_prompt(self, input_text: str) -> EasyInputMessageParam:
        """Get a file prompt that can be included in the input list."""
        pass
```

Two implementations are provided:

1. `UploadedFile`: For files that need to be uploaded to the LLM provider (e.g., PDFs)
2. `TextFile`: For text files that can be included directly in the prompt

## CLI Architecture

The CLI is built using Typer and follows a clean command structure:

### Single-shot Mode

1. Command parsing and validation
2. Settings initialization from environment and CLI options
3. LLM provider creation and configuration
4. File handling (if specified)
5. Response generation and formatting
6. Cleanup

Example flow:

```python
async def run_chat(prompt: str, settings: Settings, stream: bool = False):
    async with create_llm(settings) as llm:
        if settings.file_path:
            await llm.add_file(settings.file_path)
        
        response = await llm.respond(
            input=prompt,
            stream=stream,
            text=response_format
        )
        
        if settings.output_format == "markdown":
            logging.output(Markdown(response_text))
```

### Interactive Mode

1. Initial setup (same as single-shot)
2. Continuous prompt-response loop:
   - User input handling
   - Response streaming
   - Context maintenance
   - File cleanup on exit

Example flow:

```python
async def run_interactive_chat(initial_prompt: str, settings: Settings):
    async with create_llm(settings) as llm:
        while True:
            response = await llm.respond(input=current_prompt)
            display_response(response)
            current_prompt = get_next_prompt()
            if not current_prompt:
                break
```

## Configuration Management

Configuration is handled through Pydantic's `BaseSettings` with enhanced XDG compatibility:

```python
class Settings(BaseSettings):
    provider: Literal["openai"] = "openai"
    openai_api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o-mini", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature", ge=0.0, le=2.0)
    output_format: Literal["text", "markdown", "json"] = Field(
        default="text", description="Output format for responses"
    )
    
    # Config settings
    config_file: Path | None = Field(default=None, description="Path to config file")
    
    model_config = SettingsConfigDict(
        env_prefix="ALLEYCAT_",
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
    @model_validator(mode="after")
    def set_default_paths(self) -> "Settings":
        """Set default paths for files and directories using XDG standards."""
        app_name = "alleycat"

        # Get standard directories
        config_dir = Path(user_config_dir(app_name))
        data_dir = Path(user_data_dir(app_name))
        cache_dir = Path(user_cache_dir(app_name))

        # Set default paths if not explicitly set
        if self.config_file is None:
            self.config_file = config_dir / "config.yml"
            
        # ... other path settings ...
        
        return self
```

This provides:

- Environment variable support with `ALLEYCAT_` prefix
- .env file loading
- Type validation and coercion
- Default values
- XDG Base Directory specification compliance:
  - Config files in `~/.config/alleycat/` on Linux/macOS
  - Data files in `~/.local/share/alleycat/` on Linux/macOS
  - Appropriate Windows locations through platformdirs
- Configuration loading and saving to YAML

### Configuration Loading Priority

The system uses a cascading configuration priority:

1. **Command-line arguments** (highest priority)
2. **Environment variables** with `ALLEYCAT_` prefix
3. **Configuration file** in XDG config directory
4. **Hard-coded defaults** (lowest priority)

### Configuration Persistence

The `Settings` class includes methods for saving and loading configuration:

```python
def load_from_file(self) -> None:
    """Load settings from config file if it exists."""
    if self.config_file is None or not self.config_file.exists():
        return

    # Parse YAML file
    import yaml
    with open(str(self.config_file), encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
        
    # Update only explicitly set fields
    for key, value in config_data.items():
        if hasattr(self, key) and value is not None:
            setattr(self, key, value)

def save_to_file(self) -> None:
    """Save current settings to config file."""
    # Convert to dict, excluding None values and non-serializable objects
    config_data = {}
    for key, value in self.model_dump().items():
        if value is None or isinstance(value, Path | bytes):
            continue
        config_data[key] = value

    # Write to YAML file
    import yaml
    with open(str(self.config_file), "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False)
```

## Initialization Command Pattern

The system implements a dedicated initialization command pattern through `alleycat-admin setup`:

```python
@app.command()
def main(
    remove: bool = typer.Option(False, "--remove", "-r", help="Remove AlleyCat configuration and data files"),
) -> None:
    """Initialize AlleyCat configuration with interactive prompts."""
    # Implementation details...
```

This pattern offers two approaches to configuration:

1. **Standalone Command**: Available as `alleycat-admin setup` for direct invocation

### Integration with Main CLI

The initialization pattern is integrated with the main CLI through several mechanisms:

1. **Standalone Command**: Available as `alleycat-admin setup` for direct invocation
2. **Direct Integration**: Main command checks for `--setup` flag:
```python
@app.command()
def chat(
    # ...other parameters...
    setup: bool = typer.Option(False, "--setup", help="Run the setup wizard"),
    remove_config: bool = typer.Option(False, "--remove-config", help="Remove configuration files"),
) -> None:
    """Send a prompt to the LLM."""
    # First check if user wants to initialize or remove config
    if setup or remove_config:
        init_main(remove=remove_config)
        if not ctx.args:  # If no other arguments, exit after init
            return
```

3. **Auto-Initialization**: Main command auto-triggers initialization if no configuration exists:
```python
# Example pseudocode from main flow
settings = Settings()
settings.load_from_file()

# Check if API key is missing and prompt for initialization
if not settings.openai_api_key:
    if Confirm.ask("No API key found. Run initialization wizard?"):
        init_main(remove=False)
        settings = Settings()  # Reload settings after initialization
        settings.load_from_file()
```

### Configuration Removal

The init command also provides a way to remove configuration:

```python
if remove:
    # Display paths that will be removed
    if settings.config_file and settings.config_file.exists():
        console.print(f"Configuration file: [yellow]{settings.config_file}[/yellow]")
        
    # Ask for confirmation
    if Confirm.ask("\nAre you sure you want to remove these files?", default=False):
        # Remove files
        if settings.config_file and settings.config_file.exists():
            settings.config_file.unlink()
            
        # Remove other files as needed
```

This provides a clean way for users to:
- Remove sensitive API keys
- Reset configuration to defaults
- Clean up before uninstallation

## Output Formatting

The system supports three output formats:

1. **Text**: Plain text output
2. **Markdown**: Rich formatted output using the `rich` library
3. **JSON**: Structured data output

Output handling is managed through Rich's Console class:

```python
output_console = Console(theme=theme)
def output(message: Union[str, ConsoleRenderable], **kwargs):
    output_console.print(message, **kwargs)
```

## Testing Architecture

The testing framework includes:

1. **Unit Tests**
   - Mock LLM providers
   - File handling tests
   - Configuration validation

2. **Integration Tests**
   - CLI command testing
   - File upload/download flows
   - Response formatting

3. **Test Cases**

   ```python
   class LLMTestCase(BaseModel):
       name: str
       prompt: str
       expected_patterns: list[str]
       required_elements: list[str]
       min_score: float = 0.8
   ```

## Future Extensions

The architecture is designed to support:

1. Additional LLM providers through the `LLMProvider` interface
2. New file types via the `RemoteFile` abstraction
3. Alternative user interfaces (API, web) through the clean architecture
4. Enhanced output formats and rendering options
