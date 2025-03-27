# AlleyCat Developer's Guide

This guide provides detailed information for developers who want to contribute to or modify the AlleyCat project.

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

## Development Tools

### Testing

The project uses pytest with async support:

```bash
make test 
# or 
uv run pytest
```

### Linting

Code quality is maintained using ruff:

```bash
make lint
# or
uv run ruff check .
```

### Type Checking

Static type checking is performed using mypy:

```bash
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

## Contributing

When contributing to AlleyCat:

1. Fork the repository
2. Create a feature branch
3. Make your changes following the project's coding standards
4. Write or update tests as needed
5. Run the test suite locally
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
