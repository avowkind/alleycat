"""Tests for the LLM evaluation framework."""

import pytest
from alleycat_core.llm.evaluation import (
    ResponseEvaluation,
    LLMTestCase,
    ResponseEvaluator
)


def test_response_evaluation_validation():
    """Test ResponseEvaluation validation."""
    # Valid scores
    ResponseEvaluation(score=0.0, assessment="test")
    ResponseEvaluation(score=1.0, assessment="test")
    ResponseEvaluation(score=0.5, assessment="test")
    
    # Invalid scores
    with pytest.raises(ValueError):
        ResponseEvaluation(score=-0.1, assessment="test")
    with pytest.raises(ValueError):
        ResponseEvaluation(score=1.1, assessment="test")


def test_llm_test_case_creation():
    """Test LLMTestCase creation and validation."""
    # Minimal valid test case
    test_case = LLMTestCase(
        name="test",
        prompt="Return the number 42"
    )
    assert test_case.name == "test"
    assert test_case.prompt == "Return the number 42"
    assert test_case.min_score == 0.8  # default value
    
    # Full test case
    test_case = LLMTestCase(
        name="complete_test",
        prompt="Return a JSON with number 42",
        expected_patterns=[r'"number":\s*42'],
        required_elements=["number", "42"],
        forbidden_elements=["41", "43"],
        min_score=0.9,
        tools=["json_validator"],
        instructions="Return valid JSON",
        settings={"temperature": 0.2}
    )
    assert test_case.min_score == 0.9
    assert len(test_case.expected_patterns) == 1
    assert len(test_case.required_elements) == 2
    assert len(test_case.forbidden_elements) == 2


def test_evaluator_initialization():
    """Test ResponseEvaluator initialization."""
    # Valid initialization
    evaluator = ResponseEvaluator()
    assert evaluator.similarity_threshold == 0.8
    assert evaluator.exact_match_weight == 0.6
    assert evaluator.semantic_match_weight == 0.4
    
    # Invalid weights
    with pytest.raises(ValueError):
        ResponseEvaluator(exact_match_weight=0.7, semantic_match_weight=0.7)
    
    # Invalid threshold
    with pytest.raises(ValueError):
        ResponseEvaluator(similarity_threshold=1.5)


def test_evaluator_basic_evaluation():
    """Test basic response evaluation."""
    evaluator = ResponseEvaluator()
    test_case = LLMTestCase(
        name="number_test",
        prompt="Return the number 42",
        expected_patterns=[r"42"],
        required_elements=["42"],
        min_score=0.8
    )
    
    # Perfect match
    result = evaluator.evaluate("42", test_case)
    assert result.score == 1.0
    assert "PASS" in result.assessment
    assert len(result.matches) == 2  # pattern match and required element
    assert len(result.misses) == 0
    
    # No match
    result = evaluator.evaluate("41", test_case)
    assert result.score < test_case.min_score
    assert "FAIL" in result.assessment
    assert len(result.matches) == 0
    assert len(result.misses) == 2  # pattern miss and required element miss


def test_evaluator_forbidden_elements():
    """Test evaluation with forbidden elements."""
    evaluator = ResponseEvaluator()
    test_case = LLMTestCase(
        name="forbidden_test",
        prompt="Return a number",
        expected_patterns=[r"\d+"],
        forbidden_elements=["41", "43"]
    )
    
    # Valid response
    result = evaluator.evaluate("42", test_case)
    assert result.score == 1.0
    assert len(result.misses) == 0
    
    # Response with forbidden element
    result = evaluator.evaluate("41", test_case)
    assert result.score < 1.0
    assert any("forbidden" in miss.lower() for miss in result.misses)


def test_evaluator_complex_patterns():
    """Test evaluation with complex regex patterns."""
    evaluator = ResponseEvaluator()
    test_case = LLMTestCase(
        name="json_test",
        prompt="Return JSON with number 42",
        expected_patterns=[
            r'{\s*"number":\s*42\s*}',
            r'"number":\s*42'
        ],
        required_elements=["number", "42"]
    )
    
    # Valid JSON response
    result = evaluator.evaluate('{"number": 42}', test_case)
    assert result.score == 1.0
    assert len(result.matches) == 4  # 2 patterns + 2 required elements
    
    # Invalid JSON response
    result = evaluator.evaluate('{"value": 42}', test_case)
    assert result.score < 1.0
    assert len(result.misses) > 0


@pytest.mark.asyncio
async def test_evaluator_with_llm(openai_config):
    """Test evaluation with actual LLM response."""
    from alleycat_core.llm.openai import OpenAIProvider
    
    evaluator = ResponseEvaluator()
    test_case = LLMTestCase(
        name="number_test",
        prompt="Respond with the isolated number 42",
        expected_patterns=[r"^42$"],
        min_score=0.9,
        settings={"temperature": 0.1}  # Low temperature for consistency
    )
    
    provider = OpenAIProvider(openai_config)
    response = await provider.respond(input=test_case.prompt)
    
    result = evaluator.evaluate(response.output_text, test_case)
    assert result.score >= test_case.min_score, \
        f"LLM response evaluation failed. Score: {result.score}. Assessment: {result.assessment}" 