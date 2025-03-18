"""Tests for LLM test utilities."""

import os
from pathlib import Path
import pytest
import tempfile
import yaml

from alleycat_core.llm.test_utils import (
    load_test_cases,
    load_test_suite,
    create_test_case
)


@pytest.fixture
def test_yaml_file():
    """Create a temporary YAML file with test cases."""
    test_data = {
        "basic_tests": [
            {
                "name": "test1",
                "prompt": "Return 42",
                "expected_patterns": ["42"]
            },
            {
                "name": "test2",
                "prompt": "Return JSON",
                "expected_patterns": [r'{\s*"number":\s*42\s*}'],
                "required_elements": ["number", "42"]
            }
        ],
        "complex_tests": [
            {
                "name": "test3",
                "prompt": "Write a story",
                "expected_patterns": ["story", "end"],
                "min_score": 0.7,
                "settings": {"temperature": 0.8}
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(test_data, f)
        temp_path = f.name
        
    yield temp_path
    os.unlink(temp_path)


def test_load_test_cases(test_yaml_file):
    """Test loading test cases from YAML."""
    test_suites = load_test_cases(test_yaml_file)
    
    assert len(test_suites) == 2
    assert "basic_tests" in test_suites
    assert "complex_tests" in test_suites
    
    basic_tests = test_suites["basic_tests"]
    assert len(basic_tests) == 2
    assert basic_tests[0].name == "test1"
    assert basic_tests[0].prompt == "Return 42"
    assert basic_tests[0].expected_patterns == ["42"]
    
    assert basic_tests[1].name == "test2"
    assert "number" in basic_tests[1].required_elements
    
    complex_tests = test_suites["complex_tests"]
    assert len(complex_tests) == 1
    assert complex_tests[0].min_score == 0.7
    assert complex_tests[0].settings["temperature"] == 0.8


def test_load_test_suite(test_yaml_file):
    """Test loading a specific test suite."""
    basic_tests = load_test_suite(test_yaml_file, "basic_tests")
    assert len(basic_tests) == 2
    assert all(test.name.startswith("test") for test in basic_tests)
    
    with pytest.raises(KeyError):
        load_test_suite(test_yaml_file, "nonexistent_suite")


def test_load_test_cases_file_not_found():
    """Test handling of nonexistent YAML file."""
    with pytest.raises(FileNotFoundError):
        load_test_cases("nonexistent.yaml")


def test_create_test_case():
    """Test programmatic test case creation."""
    test_case = create_test_case(
        name="programmatic_test",
        prompt="Return 42",
        expected_patterns=["42"],
        required_elements=["42"],
        forbidden_elements=["41"],
        min_score=0.9,
        tools=["calculator"],
        instructions="Be precise",
        settings={"temperature": 0.1}
    )
    
    assert test_case.name == "programmatic_test"
    assert test_case.prompt == "Return 42"
    assert test_case.expected_patterns == ["42"]
    assert test_case.required_elements == ["42"]
    assert test_case.forbidden_elements == ["41"]
    assert test_case.min_score == 0.9
    assert test_case.tools == ["calculator"]
    assert test_case.instructions == "Be precise"
    assert test_case.settings == {"temperature": 0.1}


def test_create_test_case_defaults():
    """Test test case creation with default values."""
    test_case = create_test_case(
        name="minimal_test",
        prompt="Return 42",
        expected_patterns=["42"]
    )
    
    assert test_case.required_elements == []
    assert test_case.forbidden_elements == []
    assert test_case.min_score == 0.8
    assert test_case.tools is None
    assert test_case.instructions is None
    assert test_case.settings == {} 