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

3. **Logging** (`logging.py`)
   - Rich console output formatting
   - Themed logging levels
   - Structured output handling

### Applications (`alleycat_apps`)

The applications package contains delivery mechanisms and user interfaces:

1. **Command Line Interface** (`cli/`)
   - `main.py`: Entry point and command handling
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

Configuration is handled through Pydantic's `BaseSettings`:

```python
class Settings(BaseSettings):
    provider: Literal["openai"] = "openai"
    openai_api_key: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    output_format: Literal["text", "markdown", "json"] = "text"
    
    model_config = SettingsConfigDict(
        env_prefix="ALLEYCAT_",
        env_file=".env"
    )
```

This provides:

- Environment variable support with `ALLEYCAT_` prefix
- .env file loading
- Type validation and coercion
- Default values

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
