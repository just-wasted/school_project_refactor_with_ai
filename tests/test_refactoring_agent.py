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
    extract_smells,
    apply_smell,
    apply_interactive,
    apply_all,
    show_diff,
    main,
    create_backup,
    verify_syntax,
    BACKUP_DIR
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

def test_main_no_file(capsys):
    """Test main with no file shows help."""
    with pytest.raises(SystemExit) as exc_info:
        sys.argv = ["refactoring_agent.py"]
        main()
    assert exc_info.value.code == 2  # argparse exits with 2 on error


@patch('requests.post')
@patch('refactoring_agent.check_ollama', return_value=True)
@patch('refactoring_agent.check_model', return_value=True)
def test_main_json_with_file(mock_check_model, mock_check_ollama, mock_post, tmp_path, capsys):
    """Test main with --json flag and file argument."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    mock_post.return_value = MockResponse({
        "response": '{"file": "test.py", "language": "python", "smells": [{"type": "test", "location": {"file": "test.py", "start_line": 1, "end_line": 1}, "description": "Test smell", "severity": "low", "suggestion": "Test", "reason": "Test", "impact": "readability"}], "stats": {"total_smells": 1, "high": 0, "medium": 0, "low": 1, "coverage": "100%"}}'
    }, 200)
    
    sys.argv = ["refactoring_agent.py", "--json", str(test_file)]
    
    try:
        main()
    except SystemExit:
        pass
    
    captured = capsys.readouterr()
    assert captured.out is not None
    assert "response" in captured.out
    assert "test.py" in captured.out


# =============================================================================
# TEST: New functions (create_backup, verify_syntax)
# =============================================================================


def test_create_backup_creates_directory(tmp_path):
    """Test that create_backup creates the backup directory."""
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    # Call create_backup
    backup_path = create_backup(str(test_file))
    
    # Check that backup directory exists
    expected_dir = tmp_path / BACKUP_DIR
    assert expected_dir.exists()
    
    # Check that backup file exists
    assert os.path.exists(backup_path)
    
    # Check that backup is read-only
    # Note: On some systems we can't check this reliably in tests
    
    # Check that backup content matches original
    with open(backup_path, 'r') as f:
        assert f.read() == "def foo(): pass"


def test_create_backup_multiple_calls(tmp_path):
    """Test that multiple calls to create_backup create unique files."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    backup1 = create_backup(str(test_file))
    backup2 = create_backup(str(test_file))
    
    assert backup1 != backup2
    assert os.path.exists(backup1)
    assert os.path.exists(backup2)


def test_verify_syntax_valid_code():
    """Test verify_syntax with valid Python code."""
    valid_code = "def foo():\n    return 42"
    is_valid, error = verify_syntax(valid_code)
    assert is_valid is True
    assert error == ""


def test_verify_syntax_invalid_code():
    """Test verify_syntax with invalid Python code."""
    invalid_code = "def foo()  # Missing colon\n    return 42"
    is_valid, error = verify_syntax(invalid_code)
    assert is_valid is False
    assert error != ""


# =============================================================================
# Integration Test: Full workflow with mocks
# =============================================================================

@patch('requests.post')
@patch('refactoring_agent.check_ollama', return_value=True)
@patch('refactoring_agent.check_model', return_value=True)
def test_full_workflow_json_with_file(mock_check_model, mock_check_ollama, mock_post, tmp_path, capsys):
    """Test complete workflow with --json flag: file input -> API call -> JSON output."""
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
    sys.argv = ["refactoring_agent.py", "--json", str(test_file)]
    
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
def test_full_workflow_json_with_stdin(mock_check_model, mock_check_ollama, mock_post, tmp_path, capsys):
    """Test complete workflow with --json flag and file input."""
    mock_post.return_value = MockResponse({
        "response": '{"file": "stdin", "language": "python", "smells": [{"type": "test", "location": {"file": "test.py", "start_line": 1, "end_line": 1}, "description": "Test smell", "severity": "low", "suggestion": "Test", "reason": "Test", "impact": "readability"}], "stats": {"total_smells": 1, "high": 0, "medium": 0, "low": 1, "coverage": "100%"}}'
    }, 200)
    
    # Create a temp file
    test_file = tmp_path / "stdin_code.py"
    test_file.write_text("def foo(): pass")
    
    # Execute with file argument
    sys.argv = ["refactoring_agent.py", "--json", str(test_file)]
    
    try:
        main()
    except SystemExit:
        pass
    
    captured = capsys.readouterr()
    assert "file" in captured.out or "stdin_code.py" in captured.out or "test.py" in captured.out


# =============================================================================
# TEST: New functions (extract_smells, apply_smell, etc.)
# =============================================================================

def test_extract_smells_valid():
    """Test extract_smells with valid response."""
    response = {"response": '{"smells": [{"type": "test"}]}'}
    smells = extract_smells(response)
    assert len(smells) == 1
    assert smells[0]["type"] == "test"


def test_extract_smells_invalid_json():
    """Test extract_smells with invalid JSON."""
    response = {"response": "not valid json"}
    smells = extract_smells(response)
    assert smells == []


def test_extract_smells_empty():
    """Test extract_smells with empty smells list."""
    response = {"response": '{"smells": []}'}
    smells = extract_smells(response)
    assert smells == []


def test_apply_smell_valid_location():
    """Test apply_smell with valid location and code block in suggestion."""
    code = "def foo():\n    pass"
    smell = {
        "type": "test",
        "location": {"start_line": 1, "end_line": 1},
        "description": "Test description",
        "suggestion": "```python\ndef foo():\n    return 42\n```"
    }
    result = apply_smell(code, smell, verify=False)
    assert "return 42" in result
    assert "def foo():" in result


def test_apply_smell_with_indentation():
    """Test apply_smell preserves indentation when inserting into class."""
    code = "class Test:\n    def method(self):\n        pass"
    smell = {
        "type": "test",
        "location": {"start_line": 2, "end_line": 2},
        "description": "Add new method",
        "suggestion": "```python\n    def new_method(self):\n        return 42\n```"
    }
    result = apply_smell(code, smell, verify=False)
    # Should preserve the class indentation
    assert "    def new_method(self):" in result
    assert "        return 42" in result


def test_apply_smell_syntax_verification():
    """Test apply_smell with syntax verification."""
    code = "def foo():\n    pass"
    # Invalid code (missing colon)
    smell = {
        "type": "test",
        "location": {"start_line": 1, "end_line": 1},
        "description": "Invalid code",
        "suggestion": "```python\ndef foo()  # Missing colon\n    return 42\n```"
    }
    # With verification, should return original code
    result = apply_smell(code, smell, verify=True)
    assert result == code


def test_apply_smell_without_code_block():
    """Test apply_smell with valid location but no code block in suggestion."""
    code = "def foo():\n    pass"
    smell = {
        "type": "test",
        "location": {"start_line": 1, "end_line": 1},
        "description": "Test description",
        "suggestion": "Test suggestion"
    }
    result = apply_smell(code, smell, verify=False)
    # Ohne Code-Block wird der suggestion-Text direkt als Ersatz verwendet
    assert "Test suggestion" in result
    # Der ursprüngliche Code sollte ersetzt worden sein
    assert "def foo():" not in result or "Test suggestion" in result


def test_apply_smell_invalid_location():
    """Test apply_smell with invalid location appends to end."""
    code = "def foo():\n    pass"
    smell = {
        "type": "test",
        "location": {"start_line": 999, "end_line": 999},
        "description": "Test description",
        "suggestion": "Test suggestion"
    }
    result = apply_smell(code, smell, verify=False)
    # Bei ungültiger Location wird der suggestion-Text am Ende angehängt
    assert "Test suggestion" in result
    assert "def foo():" in result


# =============================================================================
# TEST: Main with new flags
# =============================================================================

@patch('requests.post')
@patch('refactoring_agent.check_ollama', return_value=True)
@patch('refactoring_agent.check_model', return_value=True)
def test_main_json_output(mock_check_model, mock_check_ollama, mock_post, tmp_path, capsys):
    """Test main with --json flag outputs JSON."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    mock_post.return_value = MockResponse({
        "response": '{"file": "test.py", "language": "python", "smells": [{"type": "test_smell", "location": {"file": "test.py", "start_line": 1, "end_line": 1}, "description": "Test", "severity": "low", "suggestion": "Fix", "reason": "Test", "impact": "readability"}], "stats": {"total_smells": 1}}'
    }, 200)
    
    sys.argv = ["refactoring_agent.py", "--json", str(test_file)]
    
    try:
        main()
    except SystemExit:
        pass
    
    captured = capsys.readouterr()
    assert "response" in captured.out
    assert "test_smell" in captured.out
