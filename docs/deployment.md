# Deployment Guide

## Environment Variables

AlleyCat uses a combination of environment variables for both application configuration and deployment automation.

### Application Settings Variables

These variables are used by the application itself and are prefixed with `ALLEYCAT_`:

```
ALLEYCAT_OPENAI_API_KEY=your-api-key-here
ALLEYCAT_MODEL=gpt-4o-mini
ALLEYCAT_TEMPERATURE=0.7
ALLEYCAT_MAX_TOKENS=1000
ALLEYCAT_OUTPUT_FORMAT=text
```

### Deployment Variables

These variables are used by the deployment and CI/CD processes but not by the application:

```
PYPI_TOKEN=pypi-xxxxxxxxxxxx
PYPI_USERNAME=yourusername
```

## GitHub Actions CI/CD Workflows

### Workflow Overview

AlleyCat uses GitHub Actions for continuous integration and deployment:

1. **CI Workflow** - Runs tests, linting, and checks package builds
2. **Release Workflow** - Handles version bumping and PyPI releases
3. **Classifier Update** - Keeps Python version classifiers up to date

### Common Issues and Troubleshooting

#### Missing Commands

When your CI pipeline reports errors like:

```
error: Failed to spawn: `twine`
  Caused by: No such file or directory (os error 2)
```

This usually indicates that a required command-line tool is not available. Here's how to fix it:

1. **Always use `uv sync` before using dev tools**:
   ```yaml
   steps:
     - name: Install dependencies
       run: uv sync --all-extras --dev
   ```

2. **Always prefix commands with `uv run`**:
   ```yaml
   # Correct:
   run: uv run twine check dist/*
   
   # Incorrect (may fail):
   run: twine check dist/*
   ```

3. **For tools not in your dependencies**, install them explicitly:
   ```yaml
   run: |
     uv pip install toml-cli
     uv run toml get pyproject.toml
   ```

Remember that each step in GitHub Actions runs in its own shell session, so dependencies installed in one step are available to subsequent steps.

## .env File Handling

The application's Settings class is configured to:

1. Read from a `.env` file in the project root
2. Load environment variables with the `ALLEYCAT_` prefix
3. **Ignore extra variables** that aren't defined in the Settings model

This means your `.env` file can safely contain both application variables and deployment variables without causing validation errors. The `extra="ignore"` configuration in the Settings model ensures that unrecognized variables (like `PYPI_TOKEN`) are simply ignored rather than causing validation errors.

## Testing Considerations

When writing tests that involve the Settings class:

1. Use the `clean_env` fixture to ensure a clean environment for settings tests
2. Clear both application-specific and deployment environment variables
3. Mock the `.env` file behavior to prevent tests from being affected by your local environment

Example:

```python
@pytest.fixture
def clean_env(monkeypatch):
    # Clear application variables
    for env_var in [key for key in dict(os.environ) if key.startswith("ALLEYCAT_")]:
        monkeypatch.delenv(env_var, raising=False)
    
    # Clear deployment variables
    for env_var in ["PYPI_TOKEN", "PYPI_USERNAME"]:
        monkeypatch.delenv(env_var, raising=False)
        
    # Mock .env file handling
    monkeypatch.setattr(Path, "exists", lambda _: False)
    monkeypatch.setattr(Path, "read_text", lambda *args, **kwargs: "")
```

This ensures your tests remain isolated from the environment and are reproducible. 