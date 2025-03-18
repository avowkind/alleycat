"""Tests for the AlleyCat CLI interface."""

import asyncio
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from alleycat_apps.cli.main import app
from alleycat_core.llm import Message
from alleycat_core.llm.evaluation import LLMTestCase, ResponseEvaluator


@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    return CliRunner(
        env={
            # "ALLEYCAT_OPENAI_API_KEY": "test-key",
            "ALLEYCAT_MODEL": "gpt-4o-mini",
            "ALLEYCAT_TEMPERATURE": "0.7",
            "ALLEYCAT_OUTPUT_FORMAT": "text",
        }
    )


@pytest.fixture
def evaluator():
    """Create a response evaluator."""
    return ResponseEvaluator(
        similarity_threshold=0.8, exact_match_weight=0.6, semantic_match_weight=0.4
    )


def test_command_help(cli_runner):
    """Test the command help text."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Send a prompt to the LLM" in result.stdout


def test_command_basic(cli_runner, evaluator):
    """Test the basic command with evaluation."""
    test_case = LLMTestCase(
        name="basic_number",
        prompt="Respond with the isolated number 42",
        expected_patterns=[r"^42$"],
        min_score=0.9,
        settings={"temperature": 0.1},
    )

    result = cli_runner.invoke(app, [test_case.prompt])
    assert result.exit_code == 0

    eval_result = evaluator.evaluate(result.stdout.strip(), test_case)
    assert (
        eval_result.score >= test_case.min_score
    ), f"Response evaluation failed. Score: {eval_result.score}. Assessment: {eval_result.assessment}"



@pytest.mark.skip("JSON format not currently working")
def test_command_json_response(cli_runner, evaluator):
    """Test JSON response with evaluation."""
    test_case = LLMTestCase(
        name="json_response",
        prompt='Return a JSON object with {"number": 42}',
        expected_patterns=[r'{\s*"number":\s*42\s*}', r'"number":\s*42'],
        required_elements=["number", "42"],
        min_score=0.8,
        settings={"temperature": 0.1},
    )

    result = cli_runner.invoke(
        app,
        [
            "--format",
            "json",
            test_case.prompt,
        ],
    )
    assert result.exit_code == 0

    eval_result = evaluator.evaluate(result.stdout.strip(), test_case)
    assert (
        eval_result.score >= test_case.min_score
    ), f"Response evaluation failed. Score: {eval_result.score}. Assessment: {eval_result.assessment}"


def test_command_with_instructions(cli_runner, evaluator):
    """Test command with custom instructions."""
    test_case = LLMTestCase(
        name="instruction_test",
        prompt="list some pets",
        expected_patterns=[r"(?i)dog", r"(?i)cat", r"(?i)bird"],
        required_elements=["cat", ],
        min_score=0.8,
        instructions="You are an assistant for a 5 year old child, answer questions very simply",
        settings={"temperature": 0.1},
    )

    result = cli_runner.invoke(
        app, [test_case.prompt, "--instructions", test_case.instructions]
    )
    assert result.exit_code == 0
    print(result.stdout.strip())
    eval_result = evaluator.evaluate(result.stdout.strip(), test_case)
    assert (
        eval_result.score >= test_case.min_score
    ), f"Response evaluation failed. Score: {eval_result.score}. Assessment: {eval_result.assessment}"


def test_command_with_tools(cli_runner, evaluator):
    """Test command with tools enabled."""
    test_case = LLMTestCase(
        name="calculator_test",
        prompt="What is 21 * 2?",
        expected_patterns=[r"42"],
        required_elements=["42"],
        min_score=0.9,
        tools=["calculator"],
        settings={"temperature": 0.1},
    )

    result = cli_runner.invoke(
        app, [test_case.prompt, "--tools", ",".join(test_case.tools or [])]
    )
    assert result.exit_code == 0

    eval_result = evaluator.evaluate(result.stdout.strip(), test_case)
    assert (
        eval_result.score >= test_case.min_score
    ), f"Response evaluation failed. Score: {eval_result.score}. Assessment: {eval_result.assessment}"
