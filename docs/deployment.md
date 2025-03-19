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

#### Build Artifacts Interfering with Git Operations

When running CI/CD workflows, build artifacts can sometimes cause issues with Git operations, especially when trying to commit changes. You might see errors like:

```
Changes not staged for commit:
  modified:   src/alleycat.egg-info/SOURCES.txt
  modified:   uv.lock
no changes added to commit
```

To handle this:

1. **Clean artifacts before committing**:
   ```yaml
   - name: Clean build artifacts
     run: |
       rm -rf dist/
       rm -rf src/*.egg-info/
       rm -f uv.lock
   ```

2. **Ensure proper .gitignore patterns**:
   Make sure your `.gitignore` file includes patterns for common build artifacts:
   ```
   # Python build artifacts
   dist/
   build/
   *.egg-info/
   uv.lock
   ```

3. **Proper workflow ordering**:
   - Clean or reset the repository before version bumping
   - Commit version changes first
   - Build and publish packages after commits are pushed

Remember that GitHub Actions workflows maintain state between steps, so files generated in early steps (like initial dependency installation) can interfere with later steps.

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

#### Version Bumping in GitHub Actions

AlleyCat uses a dedicated Python script located in `scripts/bump_version.py` for reliable version management in GitHub Actions. This approach provides:

1. Better maintainability by separating logic from workflow configuration
2. Improved readability and testability
3. More robust semantic version handling

The script handles:
- Reading the current version from pyproject.toml
- Parsing semantic version components
- Incrementing based on the bump type (major, minor, patch)
- Updating the pyproject.toml file
- Setting GitHub Actions outputs

Usage in GitHub Actions:
```yaml
- name: Bump version
  id: bump-version
  run: |
    python scripts/bump_version.py ${{ steps.bump-type.outputs.type }}
```

For local testing or manual version bumping, you can run:
```bash
# Dry run to see what would happen
python scripts/bump_version.py --dry-run

# Actually bump the patch version
python scripts/bump_version.py patch

# Bump to a minor version
python scripts/bump_version.py minor
```

This approach avoids common issues with shell-based version manipulation:
- More robust parsing of semantic versions
- Better handling of file content
- Reliable regex-based replacement
- Proper error handling 