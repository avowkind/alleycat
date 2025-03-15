.PHONY: venv install install-dev clean build run test lint prompt-test help

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

test: install-dev ## Run tests
	@echo "Running tests..."
	@. $(VENV_BIN)/activate && uv run pytest

lint: install-dev ## Run linting checks
	@echo "Running linters..."
	@. $(VENV_BIN)/activate && uv run ruff check . --fix
	@. $(VENV_BIN)/activate && uv run mypy src --fix-all

prompt-test: install ## Run alleycat with the test prompt
	@echo "Running alleycat with test prompt..."
	@. $(VENV_BIN)/activate && cat prompts/access-log.md | uv run alleycat --format json

run: install ## Run alleycat with arguments (usage: make run ARGS="your prompt here")
	@. $(VENV_BIN)/activate && uv run alleycat $(ARGS) 