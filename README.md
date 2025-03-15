# Cursortest

A Python project created with UV and modern best practices. Features a colorful CLI greeting application that demonstrates modern Python CLI development patterns.

## Features

- Modern CLI interface with Typer
- Rich text formatting with colors and emojis
- Type hints and strict type checking
- Comprehensive test coverage
- UV package management

## Installation

This project uses UV for dependency management. To get started:

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install the package in editable mode with development dependencies
uv pip install -e ".[dev]"
```

## Usage

The `hello-world` command provides several ways to greet users:

```bash
# Basic usage (will prompt for name)
hello-world

# Provide name directly
hello-world --name "Andrew"

# Use short form for name
hello-world -n "Andrew"

# Disable colored output
hello-world --name "Andrew" --no-color
```

## Development

### Running Tests

Run the full test suite:
```bash
pytest
```

Run tests with coverage report:
```bash
pytest --cov=src/cursortest

# For HTML coverage report
pytest --cov=src/cursortest --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_cli.py -v
```

### Code Quality

Format code:
```bash
black .
```

Type checking:
```bash
mypy .
```

Linting:
```bash
flake8
```

### Project Structure

```
cursortest/
├── src/cursortest/     # Source code
│   ├── __init__.py     # Package initialization
│   └── cli.py          # CLI implementation
├── tests/              # Test files
│   ├── test_cli.py     # CLI tests
│   └── test_cursortest.py
├── docs/               # Documentation
├── pyproject.toml      # Project configuration
└── README.md          # This file
```

## License

MIT 