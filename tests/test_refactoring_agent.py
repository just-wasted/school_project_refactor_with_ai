"""Unit tests for the KI-Refactoring-Agent."""

import pytest
import io
import sys
import os
from unittest.mock import patch, MagicMock
import requests

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from refactoring_agent import (
    read_code,
    check_ollama,
    check_model,
    call_ollama,
    format_output,
    main
)


# =============================================================================
# MOCK CLASSES
# =============================================================================

class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


# =============================================================================
# TEST: read_code
# =============================================================================

def test_read_code_from_file(tmp_path):
    """Test reading code from a file."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    result = read_code(str(test_file))
    assert result == "def foo(): pass"


def test_read_code_from_file_not_found(tmp_path):
    """Test reading from non-existent file raises error."""
    with pytest.raises(RuntimeError) as exc_info:
        read_code("/nonexistent/file.py")
    assert "Dateifehler" in str(exc_info.value)


def test_read_code_from_stdin(monkeypatch):
    """Test reading code from stdin."""
    monkeypatch.setattr('sys.stdin', io.StringIO("def bar(): pass"))
    result = read_code(None)
    assert result == "def bar(): pass"


# =============================================================================
# TEST: check_ollama
# =============================================================================

@patch('requests.get')
def test_check_ollama_available(mock_get):
    """Test Ollama availability check when server is running."""
    mock_get.return_value = MockResponse({"models": []}, 200)
    assert check_ollama() is True


@patch('requests.get')
def test_check_ollama_unavailable(mock_get):
    """Test Ollama availability check when server is down."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
    assert check_ollama() is False


# =============================================================================
# TEST: check_model
# =============================================================================

@patch('requests.get')
def test_check_model_available(mock_get):
    """Test model availability check when model exists."""
    mock_get.return_value = MockResponse({
        "models": [{"name": "qwen3-coder:30b"}, {"name": "mistral:7b"}]
    }, 200)
    assert check_model("qwen3-coder:30b") is True


@patch('requests.get')
def test_check_model_unavailable(mock_get):
    """Test model availability check when model does not exist."""
    mock_get.return_value = MockResponse({
        "models": [{"name": "qwen3-coder:30b"}]
    }, 200)
    assert check_model("nonexistent:1b") is False


@patch('requests.get')
def test_check_model_api_error(mock_get):
    """Test model availability check when API fails."""
    mock_get.side_effect = requests.exceptions.RequestException("API error")
    assert check_model("any-model") is False


# =============================================================================
# TEST: call_ollama
# =============================================================================

@patch('requests.post')
def test_call_ollama_success(mock_post):
    """Test successful Ollama API call."""
    mock_post.return_value = MockResponse({
        "response": '{"file": "test.py", "smells": []}'
    }, 200)
    
    result = call_ollama("def foo(): pass", "qwen3-coder:30b", 0.1)
    
    assert "response" in result
    mock_post.assert_called_once()
    
    # Check payload structure
    call_args = mock_post.call_args
    payload = call_args[1]['data']
    assert "model" in payload
    assert "system" in payload
    assert "prompt" in payload


@patch('requests.post')
def test_call_ollama_api_error(mock_post):
    """Test Ollama API call with connection error."""
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    with pytest.raises(RuntimeError) as exc_info:
        call_ollama("code", "model", 0.1)
    assert "Ollama API Error" in str(exc_info.value)


@patch('requests.post')
def test_call_ollama_http_error(mock_post):
    """Test Ollama API call with HTTP error."""
    mock_post.return_value = MockResponse({}, 500)
    
    with pytest.raises(RuntimeError):
        call_ollama("code", "model", 0.1)


# =============================================================================
# TEST: format_output
# =============================================================================

def test_format_output_json():
    """Test JSON output formatting."""
    response = {"response": '{"file": "test.py"}'}
    result = format_output(response, "json")
    assert "file" in result
    assert "test.py" in result


def test_format_output_text_valid_json():
    """Test text output formatting with valid JSON response."""
    response = {
        "response": '{"file": "test.py", "smells": [{"type": "long_method", "location": {"start_line": 10, "end_line": 30}, "description": "Test", "suggestion": "Fix it", "reason": "Too long"}]}'
    }
    result = format_output(response, "text")
    assert "long_method" in result
    assert "Zeile 10-30" in result
    assert "Test" in result


def test_format_output_text_invalid_json():
    """Test text output formatting with invalid JSON response."""
    response = {"response": "not valid json"}
    result = format_output(response, "text")
    assert result == "not valid json"


def test_format_output_text_empty_smells():
    """Test text output formatting with empty smells list."""
    response = {"response": '{"file": "test.py", "smells": []}'}
    result = format_output(response, "text")
    assert result == ""


# =============================================================================
# TEST: CLI argument parsing
# =============================================================================

def test_main_no_command(capsys):
    """Test main with no command shows help."""
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ["refactoring_agent.py"]
        main()
    assert exc_info.value.code == 1


@patch('requests.post')
@patch('refactoring_agent.check_ollama', return_value=True)
@patch('refactoring_agent.check_model', return_value=True)
def test_main_analyze_with_file(mock_check_model, mock_check_ollama, mock_post, tmp_path, capsys):
    """Test main with analyze command and file argument."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    mock_post.return_value = MockResponse({
        "response": '{"file": "test.py", "smells": []}'
    }, 200)
    
    sys.argv = ["refactoring_agent.py", "analyze", str(test_file)]
    
    try:
        main()
    except SystemExit:
        pass
    
    captured = capsys.readouterr()
    assert captured.out is not None
    assert "response" in captured.out


# =============================================================================
# Integration Test: Full workflow with mocks
# =============================================================================

@patch('requests.post')
@patch('refactoring_agent.check_ollama', return_value=True)
@patch('refactoring_agent.check_model', return_value=True)
def test_full_workflow_with_file(mock_check_model, mock_check_ollama, mock_post, tmp_path, capsys):
    """Test complete workflow: file input -> API call -> output."""
    # Setup
    test_file = tmp_path / "service.py"
    test_file.write_text("""
def process_data(x):
    if x > 0:
        return x * 2
    else:
        return x / 2
""")
    
    mock_post.return_value = MockResponse({
        "response": '{"file": "service.py", "language": "python", "smells": [{"type": "long_method", "location": {"file": "service.py", "start_line": 1, "end_line": 5}, "description": "Methode zu lang", "severity": "medium", "suggestion": "Extrahiere Logik", "reason": "SRP", "impact": "maintainability"}], "stats": {"total_smells": 1, "high": 0, "medium": 1, "low": 0, "coverage": "100%"}}'
    }, 200)
    
    # Execute
    sys.argv = ["refactoring_agent.py", "analyze", str(test_file), "--format", "text"]
    
    try:
        main()
    except SystemExit:
        pass
    
    # Verify
    captured = capsys.readouterr()
    assert "long_method" in captured.out
    assert "Methode zu lang" in captured.out


@patch('requests.post')
@patch('refactoring_agent.check_ollama', return_value=True)
@patch('refactoring_agent.check_model', return_value=True)
def test_full_workflow_with_stdin(mock_check_model, mock_check_ollama, mock_post, capsys):
    """Test complete workflow with stdin input."""
    mock_post.return_value = MockResponse({
        "response": '{"file": "stdin", "language": "python", "smells": [], "stats": {"total_smells": 0}}'
    }, 200)
    
    # Mock stdin
    original_stdin = sys.stdin
    sys.stdin = io.StringIO("def foo(): pass")
    
    try:
        sys.argv = ["refactoring_agent.py", "analyze"]
        main()
    except SystemExit:
        pass
    finally:
        sys.stdin = original_stdin
    
    captured = capsys.readouterr()
    assert "file" in captured.out or "stdin" in captured.out
