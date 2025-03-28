# AlleyCat - A command line tool for AI text processing

![AlleyCat](docs/alleycat.svg)

Alleycat is a command-line text processing utility that transforms input text using Large Language Models (LLMs). Like traditional Unix tools such as `awk` or `sed`, alleycat reads from standard input or command arguments and writes transformed text to standard output. Instead of using pattern matching or scripted transformations, alleycat leverages AI to interpret and modify text based on natural language instructions.

For comprehensive documentation, see [Alleycat Guide](docs/alleycat-guide.md).

## Quickstart

1. Install AlleyCat using pip:
   ```bash
   pip install alleycat
   ```

2. Set up your configuration (you'll need an OpenAI API key):
   ```bash
   alleycat-admin setup
   ```

3. Run a basic prompt:
   ```bash
   alleycat "What is the capital of France?"
   ```

4. Try using the knowledge base feature:
   ```bash
   # Create a new knowledge base
   alleycat-admin kb create my_documents
   
   # Add files to the knowledge base
   alleycat-admin kb add my_documents ~/Documents/*.pdf
   
   # Ask questions based on your documents
   alleycat --kb my_documents "What are the key points in these documents?"
   ```

5. For interactive chat mode:
   ```bash
   alleycat --chat
   ```


## Warnings

This is primarily a test project for my working with AI tools. As such it is probably not suitable for production use.  

There are other cool tools available:

* openai - if you install the sdk there is a command line which allows API calls to be made.  This is works and is definitive but not very friendly.
* claude code - lots of features and integration with the terminal and machine, can be used as a pipe or interactively. But its main purpose is a coding assistant. 
* warp terminal - not a cli an entire terminal with AI built in - great for asking for what you want.

You are responsible for any API credits required or used in using this tool. You should continue to monitor your OpenAI dashboard and remember that costs are associated with different models, number of tokens used and storage associated with vector stores.


## Project Structure

The project follows a modern Python package structure with a `src` layout:

```plaintext
alleycat/
├── src/
  ├── alleycat_apps/      # Application code
    └── cli/           # CLI interface
  └── alleycat_core/     # Core functionality
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

## Installation

AlleyCat can be installed in several ways depending on your needs:

### From PyPI (Recommended)

Install using `pip` with UV:

```bash
uv pip install alleycat
```

Or using `pipx` for isolated CLI tool installation (recommended for command-line tools):

```bash
pipx install alleycat
```

### From Source

Install directly from the GitHub repository:

```bash
uv pip install git+https://github.com/avowkind/alleycat.git
```

### Local Installation

If you've cloned the repository or downloaded the source:

```bash
cd alleycat
uv pip install .
```

After installation, you can run AlleyCat from anywhere with:

```bash
alleycat --help
```

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

After installation, you can run AlleyCat directly from the command line:

```bash
# Show help
alleycat --help

# Basic usage
alleycat "Your prompt here"

# With options
alleycat --mode markdown --temperature 0.7 "Your prompt here"
```

> **Note for developers**: When working on the codebase, you can use `uv run alleycat` during development to ensure the correct Python environment is used. or use `make activate` to setup the virtual environment (venv) and then run any of the make functions.

### First-time Setup

When you run AlleyCat for the first time (or if no configuration file is found), you'll automatically be guided through an interactive setup process that will:

1. Create necessary configuration directories following XDG standards
2. Prompt for your OpenAI API key
3. Let you select your preferred default model
4. Configure other settings like temperature and web search defaults

You can revisit this setup at any time using:

```bash
# Run the setup wizard from the separate command
alleycat-admin setup

# Or use the --setup flag with the main command
alleycat --setup
```

To remove all AlleyCat configuration files:

```bash
# Remove config using the dedicated command
alleycat-admin setup --remove

# Or with the main command
alleycat --remove-config
```

### Command Line Options

```bash
# Basic usage
alleycat "Your prompt here"
# note prompte does not need to be quoted
alleycat what is a cat

# Pipe input
echo "Your prompt" | alleycat

# With formatting options
alleycat --mode markdown --temperature 1.7 "invent a creative list of 2050 era programming languages"

# Using system instructions
alleycat -i "You are a helpful assistant" "Your prompt here"
alleycat -i prompts/custom-style.txt "Your prompt here"

# Initialize or reconfigure settings
alleycat --setup

# Remove configuration and data files
alleycat --remove-config

# Analyze a file
alleycat -f docs/alleyfacts.pdf "Summarize this document"
# Note: Currently only PDF files are supported

# Use knowledge bases
alleycat --kb my_project "What are the key components of our architecture?"
# Query multiple knowledge bases
alleycat --kb docs --kb code_examples "Compare our API design patterns"

# Use web search tool
alleycat --tool web "What is the latest news about Python?"
# Or use the simpler alias
alleycat --web "What is the latest news about Python?"
alleycat -w "What one new thing I should know about Python"

# Use file search with vector store
alleycat --tool file-search --vector-store alleycat_kb "Find information about neural networks"
# Or use the simpler aliases
alleycat --knowledge --vector-store alleycat_kb "Find information about neural networks"
alleycat -k --vector-store alleycat_kb "Find information about neural networks"

# Interactive chat mode
alleycat --chat "Hello, how are you today?"
# or start with no initial prompt
alleycat --chat
# or talk to dr johnson
alleycat --chat -i prompts/johnson.txt

## Schema based structured output in json

# Use a single schema
alleycat --schema schemas/person.schema.json "my name is andrew invent a profile for me"

# Chain multiple schemas for complex transformations - UNTESTED
# alleycat --schema-chain "extract.schema.json,transform.schema.json" "process this data"
```

Available options:
```txt
--model                       TEXT                         Model to use [env var: ALLEYCAT_MODEL] [default: None]                       
--temperature         -t      FLOAT RANGE [0.0<=x<=2.0]    Sampling temperature [default: None]                                         
--mode                -m      [text|markdown|json|schema]  Output mode (text, markdown, json) [default: None]                           
--api-key                     TEXT                         OpenAI API key [env var: ALLEYCAT_OPENAI_API_KEY] [default: None]            
--verbose             -v                                   Enable verbose debug output                                                  
--stream              -s                                   Stream the response as it's generated                                        
--chat                -c                                   Interactive chat mode with continuous conversation                           
--instructions        -i      TEXT                         System instructions (either a string or path to a file) [default: None]      
--file                -f      TEXT                         Path to a file to upload and reference in the conversation [default: None]   
--tool                -t      TEXT                         Enable specific tools (web, file-search) [default: None]                     
--web                 -w                                   Enable web search (alias for --tool web)                                     
--setup                                                    Run the setup wizard to configure AlleyCat                                   
--remove-config                                            Remove AlleyCat configuration and data files                                 
--kb                          TEXT                         Knowledge base name to use for search (can be repeated) [default: None]      
--schema                      TEXT                         Path to JSON schema file for structured output [default: None]               
--schema-chain                TEXT                         Comma-separated paths to JSON schema files for chained processing [default: None]  
--install-completion                                       Install completion for the current shell.                                    
--show-completion                                          Show completion for the current shell, to copy it or customize the installation.
--help                                                     Show this message and exit.                                                  
```


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

## Continuous Integration and Deployment

AlleyCat uses GitHub Actions for automated testing and deployment:

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

This approach ensures compliance with branch protection rules while maintaining a streamlined release process.

## License

MIT License - see LICENSE file for details.

## Why "Alleycat"?

The name "Alleycat" draws inspiration from Unix tradition and the tool's nature:

- Like the classic Unix tools `cat` and `tac`, it processes text through standard I/O
- Like an alley cat, it's agile and adaptable, transforming text in various ways
- It prowls through your text, hunting for meaning and responding with feline grace


## Future Features - Coming Soon (perhaps)

- Support for multiple LLM providers beyond OpenAI
- Chat history management with local storage
- Custom prompt templates
- Context window management
- Model parameter presets
- Command completion for shells