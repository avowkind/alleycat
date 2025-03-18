"""Test utilities for LLM testing.

This module provides utilities for loading and managing test cases for LLM testing.
It includes functions for loading test cases from YAML files and organizing them
into test suites.

Example:
    >>> test_cases = load_test_cases("tests/llm_tests.yaml")
    >>> basic_suite = test_cases["basic_tests"]
    >>> for test in basic_suite:
    ...     print(test.name)

Author: Andrew Watkins <andrew@groat.nz>

"""

from pathlib import Path
from typing import Any

import yaml

from src.alleycat_core.llm.evaluation import LLMTestCase


def load_test_cases(yaml_path: str | Path) -> dict[str, list[LLMTestCase]]:
    """Load test cases from a YAML file.

    Args:
        yaml_path: Path to the YAML file containing test cases

    Returns:
        Dictionary mapping test suite names to lists of test cases

    Example YAML structure:
        basic_tests:
          - name: "test1"
            prompt: "Return 42"
            expected_patterns: ["42"]
          - name: "test2"
            prompt: "Return JSON"
            expected_patterns: [...]

    """
    yaml_path = Path(yaml_path)
    if not yaml_path.exists():
        raise FileNotFoundError(f"Test case file not found: {yaml_path}")

    with yaml_path.open() as f:
        test_suites = yaml.safe_load(f)

    result = {}
    for suite_name, test_cases in test_suites.items():
        result[suite_name] = [LLMTestCase(**test_case) for test_case in test_cases]

    return result


def load_test_suite(yaml_path: str | Path, suite_name: str) -> list[LLMTestCase]:
    """Load a specific test suite from a YAML file.

    Args:
        yaml_path: Path to the YAML file containing test cases
        suite_name: Name of the test suite to load

    Returns:
        List of test cases in the specified suite

    Raises:
        KeyError: If the specified suite is not found

    """
    test_suites = load_test_cases(yaml_path)
    if suite_name not in test_suites:
        raise KeyError(f"Test suite '{suite_name}' not found. Available suites: {list(test_suites.keys())}")
    return test_suites[suite_name]


def create_test_case(
    name: str,
    prompt: str,
    expected_patterns: list[str],
    required_elements: list[str] | None = None,
    forbidden_elements: list[str] | None = None,
    min_score: float = 0.8,
    tools: list[str] | None = None,
    instructions: str | None = None,
    settings: dict[str, Any] | None = None,
) -> LLMTestCase:
    """Create a new test case with the specified parameters.

    This is a convenience function for creating test cases programmatically
    rather than loading them from YAML.

    Args:
        name: Unique identifier for the test case
        prompt: The prompt to send to the LLM
        expected_patterns: List of regex patterns to match
        required_elements: List of required elements (optional)
        forbidden_elements: List of forbidden elements (optional)
        min_score: Minimum score required to pass (default: 0.8)
        tools: List of tools to enable (optional)
        instructions: Custom instructions for the LLM (optional)
        settings: Additional LLM settings (optional)

    Returns:
        A new LLMTestCase instance

    """
    return LLMTestCase(
        name=name,
        prompt=prompt,
        expected_patterns=expected_patterns,
        required_elements=required_elements or [],
        forbidden_elements=forbidden_elements or [],
        min_score=min_score,
        tools=tools,
        instructions=instructions,
        settings=settings or {},
    )
