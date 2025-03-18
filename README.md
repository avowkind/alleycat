# AlleyCat - A command line tool for AI text processing

![AlleyCat](docs/alleycat.svg)
Alleycat is a command-line text processing utility that transforms input text using Large Language Models (LLMs). Like traditional Unix tools such as `awk` or `sed`, alleycat reads from standard input or command arguments and writes transformed text to standard output. Instead of using pattern matching or scripted transformations, alleycat leverages AI to interpret and modify text based on natural language instructions.

For comprehensive documentation, see [Alleycat Guide](docs/alleycat-guide.md).

Warning: very new, not all tests passing, no build or deployment etc.

## Project Structure

The project follows a modern Python package structure with a `src` layout:

```plaintext
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

The CLI tool can be run using `uv run` to ensure the correct Python environment but when running in the deployed folder you can also just use `alleycat` as it is in the pyproject.toml commands:

```bash
# Show help
uv run alleycat --help

# Basic usage
uv run alleycat "Your prompt here"

# With options
uv run alleycat --format markdown --temperature 0.7 "Your prompt here"
```

### Command Line Options

```bash
# Basic usage
alleycat "Your prompt here"

# Pipe input
echo "Your prompt" | alleycat

# With formatting options
alleycat --format markdown --temperature 0.7 "Your prompt here"

# Using system instructions
alleycat -i "You are a helpful assistant" "Your prompt here"
alleycat -i prompts/custom-style.txt "Your prompt here"
```

Available options:

- `--model`, `-m`: Choose LLM model (default: gpt-4o-mini, env: ALLEYCAT_MODEL)
- `--temperature`, `-t`: Sampling temperature 0.0-2.0 (default: 0.7)
- `--format`, `-f`: Output format - text, markdown, or json (default: text)
- `--api-key`: OpenAI API key (env: ALLEYCAT_OPENAI_API_KEY)
- `--instructions`, `-i`: System instructions (string or file path)
- `--verbose`, `-v`: Enable verbose debug output
- `--stream`, `-s`: Stream the response as it's generated

Environment variables:

- `ALLEYCAT_MODEL`: Default model to use
- `ALLEYCAT_OPENAI_API_KEY`: OpenAI API key
- `ALLEYCAT_TEMPERATURE`: Default temperature setting

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

## Why "Alleycat"?

The name "Alleycat" draws inspiration from Unix tradition and the tool's nature:

- Like the classic Unix tools `cat` and `tac`, it processes text through standard I/O
- Like an alley cat, it's agile and adaptable, transforming text in various ways
- It prowls through your text, hunting for meaning and responding with feline grace


## Future Features - Coming Soon (perhaps)

- Interactive mode for continuous conversations
- Support for multiple LLM providers beyond OpenAI
- Chat history management with local storage
- Custom prompt templates
- Streaming responses
- Context window management
- Model parameter presets
- Command completion for shells
