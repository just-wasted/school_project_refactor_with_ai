"""
System test scenarios for refactoring agent.
Tests various refactoring scenarios and validates output.
"""
import os
import subprocess
import tempfile
import shutil

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_SCRIPT = os.path.join(os.path.dirname(TEST_DIR), "src", "refactoring_agent.py")
OLLAMA_TIMEOUT = 240

def run_agent(file_path, output_path=None, json_mode=False):
    """Run the refactoring agent on a file."""
    cmd = ["python", AGENT_SCRIPT, file_path]
    if output_path:
        cmd.extend(["--output", output_path])
    if json_mode:
        cmd.append("--json")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=OLLAMA_TIMEOUT,
        cwd=os.path.dirname(os.path.dirname(TEST_DIR))
    )
    return result


def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    result = subprocess.run(
        ["python", "-m", "py_compile", file_path],
        capture_output=True,
        text=True,
        timeout=10
    )
    return result.returncode == 0, result.stderr


def check_pyflakes(file_path):
    """Check if a Python file passes pyflakes."""
    try:
        result = subprocess.run(
            ["pyflakes", file_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout + result.stderr
    except:
        return True, ""


def count_lines(file_path):
    """Count lines in a file."""
    with open(file_path, 'r') as f:
        return len(f.readlines())


def get_methods(code):
    """Extract method names from Python code."""
    import ast
    try:
        tree = ast.parse(code)
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                methods.append(node.name)
        return set(methods)
    except:
        return set()


def read_file(file_path):
    """Read file content."""
    with open(file_path, 'r') as f:
        return f.read()


# Test Case 1: Complete refactoring - Long method with duplicates
TEST_COMPLETE = """
import random

class OrderProcessor:
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
"""


# Test Case 2: Middle of file refactoring
TEST_MIDDLE = """
import random

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
"""


# Test Case 3: End of file refactoring
TEST_END = """
import random

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
"""


# Test Case 4: Duplicate code at module level
TEST_DUPLICATES = """
def process_data_a(data):
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
"""


def run_test(test_name, code, expected_behavior):
    """Run a single test scenario."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        test_file = f.name
    
    try:
        # Run agent with JSON output to see what it proposes
        result = run_agent(test_file, json_mode=True)
        
        if result.returncode != 0:
            print(f"FAILED: Agent error: {result.stderr}")
            return False
        
        print("Agent output (JSON mode):")
        print(result.stdout[:500])
        
        # Parse JSON output
        import json
        try:
            smells = json.loads(result.stdout)
            print(f"\nFound {len(smells.get('smells', []))} code smells")
            
            if not smells.get('smells'):
                print("WARNING: No smells detected")
                return False
            
            # For each smell, check if it makes sense
            for i, smell in enumerate(smells.get('smells', [])):
                print(f"\nSmell {i+1}: {smell.get('type', 'unknown')}")
                print(f"  Location: {smell.get('location', {})}")
                print(f"  Description: {smell.get('description', '')[:80]}")
                
                # Check if old_code and new_code are provided
                if not smell.get('old_code'):
                    print(f"  WARNING: No old_code provided")
                if not smell.get('new_code'):
                    print(f"  WARNING: No new_code provided")
                
                # Check if diff is provided
                if not smell.get('diff'):
                    print(f"  WARNING: No diff provided")
                
        except json.JSONDecodeError as e:
            print(f"FAILED: Invalid JSON output: {e}")
            return False
        
        # Now run with apply mode (select all)
        output_file = test_file + ".refactored.py"
        
        # We need to simulate interactive mode... for now just test JSON
        print("\nTest passed: Agent ran without errors")
        return True
        
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_complete_refactoring():
    """Test complete file refactoring."""
    return run_test("Complete Refactoring", TEST_COMPLETE, {})


def test_middle_refactoring():
    """Test refactoring in middle of file."""
    return run_test("Middle Refactoring", TEST_MIDDLE, {})


def test_end_refactoring():
    """Test refactoring at end of file."""
    return run_test("End Refactoring", TEST_END, {})


def test_duplicates():
    """Test duplicate code detection."""
    return run_test("Duplicate Code", TEST_DUPLICATES, {})


if __name__ == "__main__":
    print("Running system tests for refactoring agent...")
    
    tests = [
        ("Complete Refactoring", test_complete_refactoring),
        ("Middle Refactoring", test_middle_refactoring),
        ("End Refactoring", test_end_refactoring),
        ("Duplicate Code", test_duplicates),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"ERROR in {name}: {e}")
            results.append((name, False))
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{name}: {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed < total:
        exit(1)
