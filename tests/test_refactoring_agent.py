"""Unit tests for the KI-Refactoring-Agent."""

import pytest
import io
import sys
import os
from unittest.mock import patch
import requests

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from refactoring_agent import (
    create_backup,
    verify_syntax,
    read_code,
    check_ollama,
    check_model,
    call_ollama,
    extract_smells,
    generate_diff,
    fix_indentation,
    get_selection,
    run_pyflakes,
    apply_refactoring,
    main,
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


def test_read_code_from_file_not_found():
    """Test reading from non-existent file raises error."""
    with pytest.raises(FileNotFoundError):
        read_code("/nonexistent/file.py")


def test_read_code_from_stdin(monkeypatch):
    """Test reading code from stdin."""
    monkeypatch.setattr('sys.stdin', io.StringIO("def bar(): pass"))
    result = read_code(None)
    assert result == "def bar(): pass"


# =============================================================================
# TEST: verify_syntax
# =============================================================================

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
        "models": [{"name": "gemma4:e2b"}, {"name": "qwen2.5-coder:7b"}]
    }, 200)
    assert check_model("gemma4:e2b") is True


@patch('requests.get')
def test_check_model_unavailable(mock_get):
    """Test model availability check when model does not exist."""
    mock_get.return_value = MockResponse({
        "models": [{"name": "gemma4:e2b"}]
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
def test_call_ollama_analyze_success(mock_post):
    """Test successful Ollama API call for analyze mode."""
    import json
    mock_post.return_value = MockResponse({
        "response": '{"file": "test.py", "smells": []}'
    }, 200)
    
    result = call_ollama("def foo(): pass", "gemma4:e2b", 0.1, mode="analyze")
    
    assert "response" in result
    mock_post.assert_called_once()
    
    call_args = mock_post.call_args
    payload_data = call_args[1]['data']
    # data is JSON string, need to parse it
    payload = json.loads(payload_data)
    assert "model" in payload
    assert "system" in payload
    assert "prompt" in payload
    assert "format" in payload
    assert payload["format"] == "json"


@patch('requests.post')
def test_call_ollama_apply_success(mock_post):
    """Test successful Ollama API call for apply mode."""
    mock_post.return_value = MockResponse({
        "response": 'def foo():\n    return 42'
    }, 200)
    
    result = call_ollama("def foo(): pass", "gemma4:e2b", 0.1, mode="apply")
    
    assert "response" in result
    mock_post.assert_called_once()
    
    call_args = mock_post.call_args
    import json
    payload_data = call_args[1]['data']
    payload = json.loads(payload_data)
    assert "model" in payload
    assert "system" in payload
    assert "prompt" in payload
    # format should not be in apply mode
    assert "format" not in payload


@patch('requests.post')
def test_call_ollama_api_error(mock_post):
    """Test Ollama API call with connection error."""
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    with pytest.raises(requests.exceptions.ConnectionError):
        call_ollama("code", "model", 0.1)


# =============================================================================
# TEST: extract_smells
# =============================================================================

def test_extract_smells_valid():
    """Test extract_smells with valid response."""
    response = {"response": '{"smells": [{"type": "test", "location": {"start_line": 1, "end_line": 1}, "old_code": "def foo(): pass", "new_code": "def foo(): return 42"}]}'}
    full_code = "def foo(): pass"
    smells = extract_smells(response, full_code)
    assert len(smells) == 1
    assert smells[0]["type"] == "test"
    assert "old_code" in smells[0]
    assert "new_code" in smells[0]
    assert "diff" in smells[0]


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


# =============================================================================
# TEST: generate_diff
# =============================================================================

def test_generate_diff_simple_change():
    """Test generate_diff with simple code change."""
    old_code = "def foo():\n    pass"
    new_code = "def foo():\n    return 42"
    diff = generate_diff(old_code, new_code)
    assert "@@" in diff
    assert "-    pass" in diff
    assert "+    return 42" in diff


def test_generate_diff_no_change():
    """Test generate_diff when code is unchanged."""
    old_code = "def foo():\n    pass"
    new_code = "def foo():\n    pass"
    diff = generate_diff(old_code, new_code)
    assert diff == ""


# =============================================================================
# TEST: fix_indentation
# =============================================================================

def test_fix_indentation_method_in_class():
    """Test fix_indentation for method inside class."""
    smell = {
        "old_code": "    def process_order(self, order):\n        if order is None:\n            return None",
        "new_code": "def process_order(self, order):\n    if order is None:\n        return None\n\n    def _validate(self, order):\n        return order is not None",
    }
    full_code = "class Test:\n    def process_order(self, order):\n        if order is None:\n            return None"
    fix_indentation(smell, full_code)
    assert "    def process_order" in smell["new_code"]
    assert "        if order" in smell["new_code"]


# =============================================================================
# TEST: get_selection
# =============================================================================

def test_get_selection_all_yes(monkeypatch):
    """Test get_selection with all 'y' responses."""
    smells = [{"type": "test1"}, {"type": "test2"}]
    monkeypatch.setattr('builtins.input', lambda _: 'y')
    selected = get_selection(smells)
    assert selected == [0, 1]


def test_get_selection_skip_all(monkeypatch):
    """Test get_selection with all 'n' responses."""
    smells = [{"type": "test1"}, {"type": "test2"}]
    monkeypatch.setattr('builtins.input', lambda _: 'n')
    selected = get_selection(smells)
    assert selected == []


def test_get_selection_apply_all(monkeypatch):
    """Test get_selection with 'a' to apply all remaining."""
    smells = [{"type": "test1"}, {"type": "test2"}, {"type": "test3"}]
    responses = iter(['n', 'a'])
    monkeypatch.setattr('builtins.input', lambda _: next(responses))
    selected = get_selection(smells)
    assert selected == [1, 2]


def test_get_selection_quit(monkeypatch):
    """Test get_selection with 'q' to quit."""
    smells = [{"type": "test1"}]
    monkeypatch.setattr('builtins.input', lambda _: 'q')
    selected = get_selection(smells)
    assert selected is None


# =============================================================================
# TEST: run_pyflakes
# =============================================================================

def test_run_pyflakes_valid_code():
    """Test run_pyflakes with valid code."""
    valid_code = "def foo():\n    return 42"
    ok, error = run_pyflakes(valid_code)
    assert ok is True
    assert error == ""


def test_run_pyflakes_invalid_code():
    """Test run_pyflakes with code that has issues."""
    invalid_code = "import os\nimport sys\nx = 1"
    ok, error = run_pyflakes(invalid_code)
    assert ok is False


# =============================================================================
# TEST: apply_refactoring
# =============================================================================

@patch('requests.post')
def test_apply_refactoring_no_changes(mock_post):
    """Test apply_refactoring with no selected changes."""
    code = "def foo(): pass"
    smells = []
    result = apply_refactoring(code, smells, [], "gemma4:e2b", 0.1)
    assert result == code


@patch('requests.post')
def test_apply_refactoring_with_changes(mock_post):
    """Test apply_refactoring with selected changes."""
    code = "def foo(): pass"
    smells = [{
        "type": "test",
        "location": {"start_line": 1, "end_line": 1},
        "old_code": "def foo(): pass",
        "new_code": "def foo(): return 42"
    }]
    mock_post.return_value = MockResponse({
        "response": 'def foo():\n    return 42'
    }, 200)
    
    result = apply_refactoring(code, smells, [0], "gemma4:e2b", 0.1)
    assert "return 42" in result
    assert "def foo():" in result


# =============================================================================
# TEST: create_backup
# =============================================================================

@patch('refactoring_agent.os.makedirs')
@patch('refactoring_agent.shutil.copy2')
@patch('refactoring_agent.os.chmod')
def test_create_backup_creates_directory(mock_chmod, mock_copy2, mock_makedirs, tmp_path):
    """Test that create_backup creates the backup directory."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    backup_path = create_backup(str(test_file))
    
    mock_makedirs.assert_called_once()
    mock_copy2.assert_called_once_with(str(test_file), backup_path)
    mock_chmod.assert_called_once_with(backup_path, 0o444)
    assert backup_path.endswith("_test.py")


@patch('refactoring_agent.os.makedirs')
@patch('refactoring_agent.shutil.copy2')
@patch('refactoring_agent.os.chmod')
def test_create_backup_unique_files(mock_chmod, mock_copy2, mock_makedirs, tmp_path):
    """Test that multiple calls to create_backup create unique files."""
    import datetime as dt_module
    
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    timestamps = iter(['20240101_120000', '20240101_120001'])
    
    class MockDateTime(dt_module.datetime):
        @classmethod
        def now(cls):
            ts = next(timestamps)
            # Return a datetime that formats to our timestamp
            return dt_module.datetime.strptime(ts, "%Y%m%d_%H%M%S")
    
    with patch('refactoring_agent.datetime.datetime', MockDateTime):
        backup1 = create_backup(str(test_file))
        backup2 = create_backup(str(test_file))
    
    assert backup1 != backup2
    assert "20240101_120000" in backup1
    assert "20240101_120001" in backup2


# =============================================================================
# TEST: main function
# =============================================================================

@patch('requests.post')
@patch('refactoring_agent.check_ollama', return_value=True)
@patch('refactoring_agent.check_model', return_value=True)
def test_main_json_with_file(mock_check_model, mock_check_ollama, mock_post, tmp_path, capsys):
    """Test main with --json flag and file argument."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    # Use proper JSON string with escaped newlines
    import json as json_module
    response_json = {
        "smells": [{
            "type": "test", 
            "location": {"start_line": 1, "end_line": 1}, 
            "description": "Test smell", 
            "old_code": "def foo(): pass", 
            "new_code": "def foo(): return 42", 
            "diff": "@@ -1 +1 @@\n-old\n+new", 
            "reason": "Test", 
            "impact": "readability"
        }]
    }
    response_str = json_module.dumps(response_json)
    
    mock_post.return_value = MockResponse({
        "response": response_str
    }, 200)
    
    sys.argv = ["refactoring_agent.py", "--json", str(test_file)]
    
    try:
        main()
    except SystemExit:
        pass
    
    captured = capsys.readouterr()
    assert "test" in captured.out


@patch('requests.get')
def test_main_ollama_unavailable(mock_get, capsys, tmp_path):
    """Test main when Ollama is not available."""
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    test_file = tmp_path / "test.py"
    test_file.write_text("def foo(): pass")
    
    sys.argv = ["refactoring_agent.py", str(test_file)]
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1
    
    captured = capsys.readouterr()
    assert "Ollama nicht erreichbar" in captured.err


def test_main_no_file_shows_help(capsys):
    """Test main with no file shows help."""
    sys.argv = ["refactoring_agent.py"]
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 2
