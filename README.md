# AlleyCat

A command line tool for chat conversations with LLMs.

## Future Features

- Interactive mode for continuous conversations
- Support for multiple LLM providers beyond OpenAI
- Chat history management with local storage
- Custom prompt templates
- Streaming responses
- Context window management
- Model parameter presets
- Command completion for shells

## Project Structure

The project follows a modern Python package structure with a `src` layout:

```
alleycat/
├── src/
│   ├── alleycat_apps/      # Application code
│   │   └── cli/           # CLI interface
│   └── alleycat_core/     # Core functionality
├── tests/                 # Test files
├── pyproject.toml         # Project configuration
└── setup.py              # Development installation
```

### Package Organization

- `alleycat_apps`: Contains application-specific code
  - `cli`: Command-line interface implementation
- `alleycat_core`: Core functionality and business logic
  - `config`: Configuration management
  - `llm`: LLM integration and API handling

## Development Setup

This project uses [uv](https://github.com/astral-sh/uv) as the package manager for faster and more reliable Python package management.

### Prerequisites

- Python 3.12 or higher
- uv package manager

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd alleycat
   ```

2. Create and activate a virtual environment with uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```

3. Install the package in development mode:
   ```bash
   uv pip install -e .
   ```

4. Install development dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

## Usage

The CLI tool can be run using `uv run` to ensure the correct Python environment:

```bash
# Show help
uv run alleycat --help

# Basic usage
uv run alleycat "Your prompt here"

# With options
uv run alleycat --format markdown --temperature 0.7 "Your prompt here"
```

### Command Line Options

- `prompt`: The text prompt to send to the LLM (required)
- `--model`, `-m`: Model to use (env: ALLEYCAT_MODEL)
- `--temperature`, `-t`: Sampling temperature (0.0-2.0)
- `--format`, `-f`: Output format (text, markdown, json)
- `--api-key`: OpenAI API key (env: ALLEYCAT_OPENAI_API_KEY)

### Environment Variables

- `ALLEYCAT_MODEL`: Default model to use
- `ALLEYCAT_OPENAI_API_KEY`: OpenAI API key

## Package Management

The project uses setuptools for package management, configured in `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=61.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {"" = "src"}
packages = ["alleycat_apps", "alleycat_core"]
```

This configuration:
- Uses the `src` layout for better package isolation
- Explicitly declares packages to include
- Supports development installation with `pip install -e .`

## Development Tools

- **Testing**: pytest with async support
  ```bash
  uv run pytest
  ```

- **Linting**: ruff
  ```bash
  uv run ruff check .
  ```

- **Type Checking**: mypy
  ```bash
  uv run mypy src
  ```

## License

MIT License - see LICENSE file for details. 