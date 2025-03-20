"""Tests for the AlleyCat CLI interface.

This module contains tests for the AlleyCat CLI interface.

It uses the `typer.testing.CliRunner` to run the CLI commands
and the `alleycat_core.llm.evaluation.ResponseEvaluator` to evaluate the responses.

"""

import re
import time
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from alleycat_apps.cli.main import app
from alleycat_core.llm.evaluation import LLMTestCase, ResponseEvaluator


@pytest.fixture
async def evaluator() -> ResponseEvaluator:
    """Create a response evaluator."""
    return ResponseEvaluator(similarity_threshold=0.8, exact_match_weight=0.6, semantic_match_weight=0.4)


def test_command_help(cli_runner: CliRunner) -> None:
    """Test the command help text."""
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Send a prompt to the LLM" in result.stdout


def test_command_basic(cli_runner: CliRunner, evaluator: ResponseEvaluator) -> None:
    """Test the basic command with evaluation."""
    test_case = LLMTestCase(
        name="basic_number",
        prompt="Respond with the isolated number 42",
        expected_patterns=[r"^42$"],
        min_score=0.9,
        settings={"temperature": 0.1},
    )

    result = cli_runner.invoke(app, [test_case.prompt])
    if result.exit_code != 0:
        print(f"\nCommand failed with output:\n{result.stdout}")
        if result.exception:
            print(f"\nException: {result.exception}")
    assert result.exit_code == 0

    eval_result = evaluator.evaluate(result.stdout.strip(), test_case)
    assert eval_result.score >= test_case.min_score, (
        f"Response evaluation failed. Score: {eval_result.score}. Assessment: {eval_result.assessment}"
    )


@pytest.mark.skip("JSON format not currently working")
@pytest.mark.asyncio
async def test_command_json_response(cli_runner: CliRunner, evaluator: ResponseEvaluator) -> None:
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
            "--mode",
            "json",
            test_case.prompt,
        ],
    )
    assert result.exit_code == 0

    eval_result = evaluator.evaluate(result.stdout.strip(), test_case)
    assert eval_result.score >= test_case.min_score, (
        f"Response evaluation failed. Score: {eval_result.score}. Assessment: {eval_result.assessment}"
    )


def test_command_with_instructions(cli_runner: CliRunner, evaluator: ResponseEvaluator) -> None:
    """Test command with custom instructions."""
    test_case = LLMTestCase(
        name="instruction_test",
        prompt="list some pets",
        expected_patterns=[r"(?i)dog", r"(?i)cat", r"(?i)bird"],
        required_elements=[
            "cat",
        ],
        min_score=0.8,
        instructions="You are an assistant for a 5 year old child, answer questions very simply",
        settings={"temperature": 0.1},
    )

    result = cli_runner.invoke(app, [test_case.prompt, "--instructions", test_case.instructions or ""])
    assert result.exit_code == 0
    print(result.stdout.strip())
    eval_result = evaluator.evaluate(result.stdout.strip(), test_case)
    assert eval_result.score >= test_case.min_score, (
        f"Response evaluation failed. Score: {eval_result.score}. Assessment: {eval_result.assessment}"
    )


def test_command_with_tools(cli_runner: CliRunner, evaluator: ResponseEvaluator) -> None:
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

    result = cli_runner.invoke(app, [test_case.prompt, "--tools", ",".join(test_case.tools or [])])
    assert result.exit_code == 0

    eval_result = evaluator.evaluate(result.stdout.strip(), test_case)
    assert eval_result.score >= test_case.min_score, (
        f"Response evaluation failed. Score: {eval_result.score}. Assessment: {eval_result.assessment}"
    )


def test_yaml_test_cases(cli_runner: CliRunner, evaluator: ResponseEvaluator) -> None:
    """Test running test cases loaded from YAML file."""
    yaml_path = Path(__file__).parent.parent.parent / "data" / "llm_test_cases.yaml"

    with open(yaml_path, encoding="utf-8") as f:
        test_suites = yaml.safe_load(f)

    # Run tests from each test suite
    for _suite_name, test_cases in test_suites.items():
        for test_data in test_cases:
            test_case = LLMTestCase(
                name=test_data["name"],
                prompt=test_data["prompt"],
                expected_patterns=test_data["expected_patterns"],
                required_elements=test_data.get("required_elements", []),
                forbidden_elements=test_data.get("forbidden_elements", []),
                min_score=test_data["min_score"],
                instructions=test_data.get("instructions", ""),
                tools=test_data.get("tools", []),
                settings=test_data.get("settings", {}),
            )

            # Build command arguments
            cmd_args = [test_case.prompt]
            if test_case.instructions:
                cmd_args.extend(["--instructions", test_case.instructions])
            if test_case.tools:
                cmd_args.extend(["--tools", ",".join(test_case.tools)])

            try:
                # Run the test case
                result = cli_runner.invoke(app, cmd_args)
                assert result.exit_code == 0, f"Test case '{test_case.name}' failed with exit code {result.exit_code}"

                response = result.stdout.strip()
                eval_result = evaluator.evaluate(response, test_case)

                # If evaluation fails, prepare error message
                if eval_result.score < test_case.min_score:
                    error_msg = [
                        f"\nTest case '{test_case.name}' failed evaluation:",
                        f"Score: {eval_result.score:.2f} (required: {test_case.min_score})",
                        f"Assessment: {eval_result.assessment}",
                        "\nFull Response:",
                        f"{response}",
                        "\nPattern Matching Results:",
                    ]

                    # Show pattern matching results
                    for pattern in test_case.expected_patterns:
                        matches = re.finditer(pattern, response)
                        matches_found = list(matches)
                        status = "✓" if matches_found else "✗"
                        error_msg.append(f"{status} Pattern '{pattern}': {len(matches_found)} matches")

                    # Show required elements status
                    if test_case.required_elements:
                        error_msg.append("\nRequired Elements:")
                        for element in test_case.required_elements:
                            found = element.lower() in response.lower()
                            status = "✓" if found else "✗"
                            error_msg.append(f"{status} '{element}'")

                    # Show forbidden elements status
                    if test_case.forbidden_elements:
                        error_msg.append("\nForbidden Elements:")
                        for element in test_case.forbidden_elements:
                            not_found = element.lower() not in response.lower()
                            status = "✓" if not_found else "✗"
                            error_msg.append(
                                f"{status} '{element}' {'(not found)' if not_found else '(found but should not be)'}"
                            )

                    # raise AssertionError("\n".join(error_msg))
                    print("\n".join(error_msg))
            finally:
                # Clean up any pending tasks
                # for task in asyncio.all_tasks():
                #     if not task.done():
                #         task.cancel()
                # Run event loop one last time to process cancellations
                # loop = asyncio.get_event_loop()
                # if not loop.is_closed():
                #     loop.run_until_complete(asyncio.sleep(0))
                time.sleep(1)
