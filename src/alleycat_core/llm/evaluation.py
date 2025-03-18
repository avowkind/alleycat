"""Evaluation module for Large Language Model (LLM) responses.

This module provides functionality for evaluating LLM responses against defined test cases
and criteria. It includes classes for test case definition, response evaluation, and
evaluation execution.

The module supports:
- Defining test cases with expected patterns and required/forbidden elements
- Evaluating responses against defined criteria
- Scoring responses based on match quality
- Tracking matched and missed criteria

Classes:
    ResponseEvaluation: Results container for an LLM response evaluation
    LLMTestCase: Definition structure for an LLM test case
    ResponseEvaluator: Main class for evaluating LLM responses

Author: Andrew Watkins <andrew@groat.nz>
"""

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field


@dataclass
class ResponseEvaluation:
    """Results of evaluating an LLM response."""

    score: float  # 0.0 to 1.0
    assessment: str
    matches: list[str] = field(default_factory=list)  # what criteria were matched
    misses: list[str] = field(default_factory=list)  # what criteria were missed
    response_text: str = ""  # actual response for reference

    def __post_init__(self) -> None:
        """Validate the score is between 0 and 1."""
        if not 0 <= self.score <= 1:
            raise ValueError("Score must be between 0 and 1")


class LLMTestCase(BaseModel):
    """Definition of an LLM test case."""

    name: str = Field(..., description="Unique identifier for the test case")
    prompt: str = Field(..., description="The prompt to send to the LLM")
    expected_patterns: list[str] = Field(
        default_factory=list, description="List of regex patterns or exact matches to look for"
    )
    required_elements: list[str] = Field(
        default_factory=list, description="List of elements that must be present in the response"
    )
    forbidden_elements: list[str] = Field(
        default_factory=list, description="List of elements that must not be present in the response"
    )
    min_score: float = Field(default=0.8, ge=0.0, le=1.0, description="Minimum score required for the test to pass")
    tools: list[str] | None = Field(default=None, description="List of tools that should be available")
    instructions: str | None = Field(default=None, description="Custom instructions for the LLM")
    settings: dict[str, Any] = Field(
        default_factory=dict, description="Additional settings for the LLM (temperature, etc.)"
    )


class ResponseEvaluator:
    """Evaluates LLM responses against test cases."""

    def __init__(
        self,
        similarity_threshold: float = 0.8,
        exact_match_weight: float = 0.6,
        semantic_match_weight: float = 0.4,
    ):
        """Initialize the evaluator.

        Args:
            similarity_threshold: Threshold for semantic similarity (0.0 to 1.0)
            exact_match_weight: Weight for exact pattern matches in scoring
            semantic_match_weight: Weight for semantic similarity in scoring

        """
        self.similarity_threshold = similarity_threshold
        self.exact_match_weight = exact_match_weight
        self.semantic_match_weight = semantic_match_weight

        if not (0 <= similarity_threshold <= 1):
            raise ValueError("Similarity threshold must be between 0 and 1")
        if exact_match_weight + semantic_match_weight != 1.0:
            raise ValueError("Weights must sum to 1.0")

    def evaluate(self, response_text: str, test_case: LLMTestCase) -> ResponseEvaluation:
        """Evaluate a response against a test case.

        Args:
            response_text: The text response from the LLM
            test_case: The test case to evaluate against

        Returns:
            ResponseEvaluation containing the evaluation results

        """
        matches = []
        misses = []

        # Check pattern matches
        pattern_scores = []
        for pattern in test_case.expected_patterns:
            if re.search(pattern, response_text, re.MULTILINE):
                matches.append(f"Pattern match: {pattern}")
                pattern_scores.append(1.0)
            else:
                misses.append(f"Missing pattern: {pattern}")
                pattern_scores.append(0.0)

        # Check required elements
        required_scores = []
        for element in test_case.required_elements:
            if element.lower() in response_text.lower():
                matches.append(f"Required element present: {element}")
                required_scores.append(1.0)
            else:
                misses.append(f"Missing required element: {element}")
                required_scores.append(0.0)

        # Check forbidden elements
        forbidden_found = []
        for element in test_case.forbidden_elements:
            if element.lower() in response_text.lower():
                misses.append(f"Forbidden element present: {element}")
                forbidden_found.append(element)

        # Calculate score
        pattern_score = (sum(pattern_scores) / len(pattern_scores)) if pattern_scores else 1.0
        required_score = (sum(required_scores) / len(required_scores)) if required_scores else 1.0
        forbidden_penalty = len(forbidden_found) * 0.2  # 20% penalty per forbidden element

        # Combine scores with weights
        final_score = (pattern_score * self.exact_match_weight + required_score * self.semantic_match_weight) * (
            1.0 - forbidden_penalty
        )
        final_score = max(0.0, min(1.0, final_score))  # Clamp between 0 and 1

        # Generate assessment
        assessment = self._generate_assessment(
            final_score, test_case.min_score, len(matches), len(misses), forbidden_found
        )

        return ResponseEvaluation(
            score=final_score, assessment=assessment, matches=matches, misses=misses, response_text=response_text
        )

    def _generate_assessment(
        self, score: float, min_score: float, num_matches: int, num_misses: int, forbidden_found: list[str]
    ) -> str:
        """Generate a human-readable assessment of the evaluation.

        Args:
            score: The final evaluation score
            min_score: The minimum required score
            num_matches: Number of successful matches
            num_misses: Number of missing elements
            forbidden_found: List of forbidden elements that were found

        Returns:
            A string describing the evaluation results

        """
        parts = []

        if score >= min_score:
            parts.append(f"PASS (score: {score:.2f} >= {min_score:.2f})")
        else:
            parts.append(f"FAIL (score: {score:.2f} < {min_score:.2f})")

        parts.append(f"Matched {num_matches} criteria")

        if num_misses > 0:
            parts.append(f"Missing {num_misses} criteria")

        if forbidden_found:
            parts.append(f"Found {len(forbidden_found)} forbidden elements")

        return " | ".join(parts)
