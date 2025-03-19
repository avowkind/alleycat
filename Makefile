.PHONY: venv install install-dev clean build run test lint prompt-test help build-dist publish-test publish bump-version

# Use bash for shell commands
SHELL := /bin/bash

# Python settings
PYTHON_VERSION := 3.12
VENV := .venv
VENV_BIN := $(VENV)/bin

# Default target
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage:'
	@echo '  make <target>'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

$(VENV)/bin/activate: ## Create virtual environment if it doesn't exist
	@echo "Creating virtual environment..."
	@command -v uv >/dev/null 2>&1 || { echo >&2 "uv is required but not installed. Install with 'pip install uv'."; exit 1; }
	@uv venv $(VENV)
	@echo "Virtual environment created at $(VENV)"

venv: $(VENV)/bin/activate ## Create/update virtual environment

install: venv ## Install package in development mode
	@echo "Installing package..."
	@. $(VENV_BIN)/activate && uv pip install -e .

install-dev: venv ## Install package with development dependencies
	@echo "Installing package with development dependencies..."
	@. $(VENV_BIN)/activate && uv pip install -e ".[dev]"

clean: ## Clean build artifacts and virtual environment
	@echo "Cleaning build artifacts..."
	@rm -rf build/ dist/ *.egg-info/ .eggs/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/ .ruff_cache/
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Cleaning virtual environment..."
	@rm -rf $(VENV)

build: clean install ## Clean and rebuild the package
	@echo "Build complete"

# Find all source files
PACKAGE_FILES := $(shell find src -type f -name "*.py") pyproject.toml README.md

bump-version: ## Bump version number (usage: make bump-version [BUMP=patch|minor|major])
	@echo "Bumping version..."
	@BUMP_TYPE=$${BUMP:-patch}; \
	echo "Bump type: $$BUMP_TYPE"; \
	. $(VENV_BIN)/activate && uv run python scripts/bump_version.py $$BUMP_TYPE
	@uv sync --all-extras --dev
	@echo "Version bumped. Don't forget to commit the changes!"

dist: $(PACKAGE_FILES) install-dev ## Build distribution packages if source files have changed
	@echo "Building distribution packages..."
	@. $(VENV_BIN)/activate && uv build
	@touch dist

build-dist: dist ## Build distribution packages (only if needed)
	@echo "Distribution packages are up to date"

publish-test: dist ## Upload package to TestPyPI
	@echo "Uploading package to TestPyPI..."
	@. $(VENV_BIN)/activate && \
		if [ -f .env ]; then export $$(grep -v '^#' .env | xargs); fi && \
		echo "Using token from TESTPYPI_TOKEN (not showing value for security)" && \
		twine upload --repository-url https://test.pypi.org/legacy/ dist/* -u "__token__" -p $$TESTPYPI_TOKEN --verbose

publish: dist ## Upload package to PyPI
	@echo "Uploading package to PyPI..."
	@. $(VENV_BIN)/activate && \
		if [ -f .env ]; then export $$(grep -v '^#' .env | xargs); fi && \
		echo "Using token from PYPI_TOKEN (not showing value for security)" && \
		twine upload dist/* -u "__token__" -p $$PYPI_TOKEN

test: install-dev ## Run tests
	@echo "Running tests..."
	@. $(VENV_BIN)/activate && uv run pytest

lint: install-dev ## Run linting checks
	@echo "Running linters..."
	@. $(VENV_BIN)/activate && uv run ruff check . --fix
	@. $(VENV_BIN)/activate && uv run mypy src

prompt-test: install ## Run alleycat with the test prompt
	@echo "Running alleycat with test prompt..."
	@. $(VENV_BIN)/activate && cat prompts/access-log.md | uv run alleycat 

run: install ## Run alleycat with arguments (usage: make run ARGS="your prompt here")
	@. $(VENV_BIN)/activate && uv run alleycat $(ARGS) 