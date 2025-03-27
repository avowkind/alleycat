# Alleycat Developer's Guide

This comprehensive guide provides both practical development information and detailed technical reference for developers who want to contribute to or modify the Alleycat project.

## Quick Start

### Prerequisites

- Python 3.12 or higher
- uv package manager ([uv](https://github.com/astral-sh/uv))

### Installation Steps

1. Clone the repository and change to the project directory:

   ```bash
   git clone https://github.com/avowkind/alleycat.git
   cd alleycat
   ```

2. Create and activate a virtual environment using Python 3.12:

   ```bash
   # with UV
   uv sync --all-extras --dev
   .venv/bin/activate

   # or traditional
   python3.12 -m venv .venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. Install the package in development mode with dependencies:

   ```bash
   uv sync --all-extras --dev
   ```

4. Set up your OpenAI API key:

   ```bash
   export ALLEYCAT_OPENAI_API_KEY="your-api-key"
   # or add to .env file:
   echo "ALLEYCAT_OPENAI_API_KEY=your-api-key" > .env

   # note this is not required if you first run alleycat-init to store your key in the config settings
   ```

5. Verify the installation:

   ```bash
   alleycat Hello, Alleycat!
   ```

> **Note for developers**: When working on the codebase, you can use `uv run alleycat` during development to ensure the correct Python environment is used, or use `make activate` to setup the virtual environment (venv) and then run any of the make functions.

## Project Architecture

### Package Structure

The project follows a clean architecture pattern with a modern Python package structure and clear separation of concerns:

```plaintext
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

## Development Tools and Workflow

### Testing

The project uses pytest with async support:

```bash
make test 
# or 
uv run pytest
```

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

### Linting and Type Checking

Code quality is maintained using:

```bash
# Linting with ruff
make lint
# or
uv run ruff check .

# Type checking with mypy
uv run mypy src
```

## Configuration Management

### Settings Class

The project uses a Pydantic-based Settings class for configuration management:

```python
class Settings(BaseSettings):
    provider: Literal["openai"] = "openai"
    openai_api_key: str = Field(default="", description="OpenAI API key")
    model: str = Field(default="gpt-4o-mini", description="Model to use")
    temperature: float = Field(default=0.7, description="Sampling temperature", ge=0.0, le=2.0)
    output_format: Literal["text", "markdown", "json"] = Field(
        default="text", description="Output format for responses"
    )
    
    model_config = SettingsConfigDict(
        env_prefix="ALLEYCAT_",
        env_file=".env",
        env_file_encoding="utf-8"
    )
```

### Configuration Loading Priority

The system uses a cascading configuration priority:

1. Command-line arguments (highest priority)
2. Environment variables with `ALLEYCAT_` prefix
3. Configuration file in XDG config directory
4. Hard-coded defaults (lowest priority)

### Configuration File Locations

AlleyCat follows the XDG Base Directory Specification:

- **Linux/macOS**: `~/.config/alleycat/config.yml`
- **Windows**: `%APPDATA%\alleycat\config.yml`

## Continuous Integration and Deployment

### CI Workflow

A CI workflow runs on all pull requests and pushes to the main branch:

- Runs tests on Python 3.12
- Lints code with Ruff
- Type checks with mypy
- Verifies the package builds correctly

### Release Process

AlleyCat uses semantic versioning with a 2-step manual-bump and automated-release process:

1. **Manual Version Bump** (before creating PR):
   - Run `make bump-version` to increment patch version (default)
   - Or specify version type: `make bump-version BUMP=minor`
   - Commit the version change with your other changes
   - Create a PR to main

2. **Automated Release** (after PR is merged):
   - When the PR is merged, a GitHub Action:
     - Reads the current version from pyproject.toml
     - Creates a Git tag for the version
     - Builds and publishes the package to PyPI
     - Creates a GitHub release with release notes

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

## Future Extensions

The architecture is designed to support:

1. Additional LLM providers through the `LLMProvider` interface
2. New file types via the `RemoteFile` abstraction
3. Alternative user interfaces (API, web) through the clean architecture
4. Enhanced output formats and rendering options

## License

MIT License - see LICENSE file for details.
