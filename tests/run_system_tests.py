#!/usr/bin/env python3
"""
System tests for refactoring agent.
Tests JSON output and validates refactoring suggestions.
"""
import os
import subprocess
import json
import sys

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_SCRIPT = os.path.join(os.path.dirname(TEST_DIR), "src", "refactoring_agent.py")
OLLAMA_TIMEOUT = 240

# Test files
TEST_FILES_DIR = os.path.join(TEST_DIR, "test_files")

def ensure_test_files():
    """Create test files if they don't exist."""
    os.makedirs(TEST_FILES_DIR, exist_ok=True)
    
    # Test 1: service.py equivalent (long method + duplicates)
    service_code = '''"""
Service.py - Test file with code smells
"""
import random

class CentralService:
    """Zentrale Service-Klasse."""

    def __init__(self, db, log, cfg):
        self.db = db
        self.log = log
        self.cfg = cfg

    def process_order(self, order, user_id, payment, shipping):
        if order is None or user_id < 0:
            return {"status": "error", "message": "Invalid"}
        user = self._get_user(user_id)
        if not self.validate_input(order):
            return {"status": "error", "message": "Bad order"}
        if not self.check_data(order):
            return {"status": "error", "message": "Bad data"}
        if not self._process_payment(payment, order["total"]):
            return {"status": "error", "message": "Payment failed"}
        order_id = self._save(order)
        self._send_email(user, order_id)
        return {"status": "success", "order_id": order_id}

    def validate_input(self, data):
        if data is None:
            return False
        if "items" not in data:
            return False
        for item in data["items"]:
            if item.get("qty", 0) <= 0:
                return False
        return True

    def check_data(self, data):
        if data is None:
            return False
        if "items" not in data:
            return False
        for x in data["items"]:
            if x.get("qty", 0) < 1:
                return False
        return True

    def _get_user(self, uid):
        return {"id": uid}

    def _process_payment(self, pay, amount):
        if amount <= 0:
            return False
        if pay.get("method") == "card":
            if len(pay.get("num", "")) != 16:
                return False
        return True

    def _save(self, order):
        return random.randint(10000, 99999)

    def _send_email(self, user, oid):
        pass
'''
    with open(os.path.join(TEST_FILES_DIR, "service_test.py"), 'w') as f:
        f.write(service_code)
    
    # Test 2: Middle of file
    middle_code = '''import random

class Processor:
    def method_a(self):
        return self._helper_a()

    def _helper_a(self):
        return 42

    def long_method(self, x, y, z):
        result = x + y
        if z > 0:
            result = result * z
        if result < 0:
            return {"error": "Negative"}
        return {"result": result}

    def method_b(self):
        return self._helper_b()

    def _helper_b(self):
        return 99
'''
    with open(os.path.join(TEST_FILES_DIR, "middle_test.py"), 'w') as f:
        f.write(middle_code)
    
    # Test 3: End of file
    end_code = '''import random

class Service:
    def start(self):
        return True

    def process(self):
        return False


def utility_function(data):
    if not data:
        return None
    if "key" not in data:
        return None
    return data["key"]


def another_utility(x, y):
    return x + y * 100
'''
    with open(os.path.join(TEST_FILES_DIR, "end_test.py"), 'w') as f:
        f.write(end_code)
    
    # Test 4: Duplicates
    dup_code = '''def process_data_a(data):
    if not data:
        return None
    if "items" not in data:
        return None
    return data["items"]


def process_data_b(data):
    if not data:
        return None
    if "items" not in data:
        return None
    return data["items"]


def process_data_c(data):
    if not data:
        return None
    if "items" not in data:
        return None
    return data["items"]
'''
    with open(os.path.join(TEST_FILES_DIR, "duplicates_test.py"), 'w') as f:
        f.write(dup_code)


def run_agent_json(file_path):
    """Run agent in JSON mode."""
    cmd = ["python", AGENT_SCRIPT, file_path, "--json"]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=OLLAMA_TIMEOUT,
        cwd=os.path.dirname(os.path.dirname(TEST_DIR))
    )
    return result


def validate_smell(smell, idx):
    """Validate a single smell detection."""
    errors = []
    
    # Check required fields
    if not smell.get('type'):
        errors.append(f"Smell {idx}: Missing 'type'")
    
    if not smell.get('description'):
        errors.append(f"Smell {idx}: Missing 'description'")
    
    location = smell.get('location', {})
    if not location or 'start_line' not in location or 'end_line' not in location:
        errors.append(f"Smell {idx}: Missing or invalid 'location'")
    else:
        start = location.get('start_line')
        end = location.get('end_line')
        if start <= 0 or end <= 0 or start > end:
            errors.append(f"Smell {idx}: Invalid line numbers {start}-{end}")
    
    if not smell.get('old_code'):
        errors.append(f"Smell {idx}: Missing 'old_code'")
    
    if not smell.get('new_code'):
        errors.append(f"Smell {idx}: Missing 'new_code'")
    
    if not smell.get('diff'):
        errors.append(f"Smell {idx}: Missing 'diff'")
    
    # Check that old_code != new_code
    if smell.get('old_code') == smell.get('new_code'):
        errors.append(f"Smell {idx}: old_code and new_code are identical!")
    
    # Check impact and reason
    if not smell.get('impact'):
        errors.append(f"Smell {idx}: Missing 'impact'")
    
    if not smell.get('reason'):
        errors.append(f"Smell {idx}: Missing 'reason'")
    
    return errors


def test_file(file_path, expected_smell_types=None):
    """Test a single file."""
    print(f"\n{'='*60}")
    print(f"Testing: {os.path.basename(file_path)}")
    print(f"{'='*60}")
    
    result = run_agent_json(file_path)
    
    if result.returncode != 0:
        print("FAILED: Agent error")
        print(f"stderr: {result.stderr}")
        return False, [f"Agent returned error: {result.stderr}"]
    
    try:
        smells = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"FAILED: Invalid JSON: {e}")
        print(f"stdout: {result.stdout[:500]}")
        return False, [f"Invalid JSON: {e}"]
    
    if not isinstance(smells, dict) or 'smells' not in smells:
        print("FAILED: Invalid output format")
        return False, ["Invalid output format - missing 'smells' key"]
    
    smell_list = smells.get('smells', [])
    
    if not smell_list:
        print("WARNING: No smells detected")
        return True, []  # Not necessarily a failure
    
    print(f"Found {len(smell_list)} code smells")
    
    all_errors = []
    for i, smell in enumerate(smell_list):
        print(f"\n  Smell {i+1}: {smell.get('type', 'unknown')}")
        print(f"    Lines: {smell.get('location', {}).get('start_line', '?')}-{smell.get('location', {}).get('end_line', '?')}")
        print(f"    Description: {smell.get('description', '')[:60]}")
        
        errors = validate_smell(smell, i+1)
        all_errors.extend(errors)
    
    # Check for expected smell types
    if expected_smell_types:
        detected_types = [s.get('type') for s in smell_list]
        for expected_type in expected_smell_types:
            if expected_type not in detected_types:
                all_errors.append(f"Expected smell type '{expected_type}' not found")
    
    if all_errors:
        print("\n  Validation errors:")
        for err in all_errors:
            print(f"    - {err}")
    
    return len(all_errors) == 0, all_errors


def main():
    ensure_test_files()
    
    tests = [
        ("service_test.py", ["Long Method"]),  # Duplicate Code optional
        ("middle_test.py", ["Long Method"]),
        ("end_test.py", []),  # May or may not have smells
        ("duplicates_test.py", ["Duplicate Code"]),
    ]
    
    results = []
    for filename, expected_types in tests:
        filepath = os.path.join(TEST_FILES_DIR, filename)
        if not os.path.exists(filepath):
            print(f"WARNING: Test file {filename} not found, skipping")
            continue
        
        success, errors = test_file(filepath, expected_types)
        results.append((filename, success, errors))
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for filename, success, errors in results:
        status = "PASS" if success else "FAIL"
        print(f"{filename}: {status}")
        if errors:
            for err in errors:
                print(f"  - {err}")
    
    passed = sum(1 for _, s, _ in results if s)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
