#!/usr/bin/env python3
"""Direct test of apply_refactoring function."""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from refactoring_agent import (
    call_ollama,
    apply_refactoring,
    verify_syntax,
    run_pyflakes,
    extract_smells,
    deduplicate_smells,
    SMELL_TYPES,
)

MODEL = "gemma4:e2b"
TEMP = 0.1

# Test code with known smell
TEST_CODE = '''"""Simple test with duplicate code."""

class Cleaner:
    def clean_name(self, name):
        if not name:
            return ""
        name = name.strip()
        name = name.replace("  ", " ")
        return name

    def clean_address(self, address):
        if not address:
            return ""
        address = address.strip()
        address = address.replace("  ", " ")
        return address
'''

def test_apply_with_manual_smell():
    """Test apply with manually created smell (bypassing analysis)."""
    print("=" * 70)
    print("DIRECT APPLY TEST: Manual smell definition")
    print("=" * 70)
    
    # Define the smell manually (what analysis SHOULD return)
    smells = [{
        "type": "Duplicate Code",
        "location": {"start_line": 4, "end_line": 18},
        "old_code": """    def clean_name(self, name):
        if not name:
            return ""
        name = name.strip()
        name = name.replace("  ", " ")
        return name

    def clean_address(self, address):
        if not address:
            return ""
        address = address.strip()
        address = address.replace("  ", " ")
        return address""",
        "new_code": """    def _clean_text(self, text):
        if not text:
            return ""
        text = text.strip()
        text = text.replace("  ", " ")
        return text

    def clean_name(self, name):
        return self._clean_text(name)

    def clean_address(self, address):
        return self._clean_text(address)""",
        "reason": "Both methods have identical logic",
        "impact": "maintainability"
    }]
    
    print("Original code:")
    print("-" * 70)
    print(TEST_CODE)
    print("-" * 70)
    
    print("\nSmell to apply:")
    print(f"Type: {smells[0]['type']}")
    print(f"Location: {smells[0]['location']}")
    print(f"\nOld code:\n{smells[0]['old_code']}")
    print(f"\nNew code:\n{smells[0]['new_code']}")
    
    # Apply the refactoring
    print("\nApplying refactoring...")
    refactored = apply_refactoring(TEST_CODE, smells, [0], MODEL, TEMP)
    
    print("\nRefactored code:")
    print("-" * 70)
    print(refactored)
    print("-" * 70)
    
    # Verify
    print("\nVerification:")
    
    # Check syntax
    ok, err = verify_syntax(refactored)
    print(f"- Syntax: {'OK' if ok else 'FAILED: ' + err}")
    
    # Check pyflakes
    ok2, err2 = run_pyflakes(refactored)
    print(f"- Pyflakes: {'OK' if ok2 else 'FAILED: ' + err2}")
    
    # Check old code removed
    old_present = smells[0]['old_code'].strip() in refactored
    print(f"- Old code removed: {'FAILED (still present)' if old_present else 'OK'}")
    
    # Check new code added
    new_present = "_clean_text" in refactored and "def clean_name" in refactored and "self._clean_text" in refactored
    print(f"- New code added: {'OK' if new_present else 'FAILED'}")
    
    # Check call sites updated
    calls_updated = "self._clean_text(name)" in refactored and "self._clean_text(address)" in refactored
    print(f"- Call sites updated: {'OK' if calls_updated else 'FAILED'}")
    
    # Check behavior preservation
    # We can't run the code easily, but we can check structure
    has_clean_name = "def clean_name" in refactored
    has_clean_address = "def clean_address" in refactored
    print(f"- Original methods preserved: {'OK' if has_clean_name and has_clean_address else 'FAILED'}")
    
    return refactored


def test_apply_single_helper_insertion():
    """Test that helper methods are inserted at correct location."""
    print("\n" + "=" * 70)
    print("TEST: Helper method insertion location")
    print("=" * 70)
    
    code = '''"""Test class."""

class Processor:
    def __init__(self):
        self.value = 0

    def process(self, data):
        if not data:
            return None
        result = data.strip()
        result = result.replace("  ", " ")
        return result
'''
    
    smells = [{
        "type": "Long Method",
        "location": {"start_line": 6, "end_line": 12},
        "old_code": """    def process(self, data):
        if not data:
            return None
        result = data.strip()
        result = result.replace("  ", " ")
        return result""",
        "new_code": """    def process(self, data):
        if not data:
            return None
        return self._clean(data)

    def _clean(self, text):
        result = text.strip()
        result = result.replace("  ", " ")
        return result""",
        "reason": "Extract cleaning logic",
        "impact": "readability"
    }]
    
    print("Original code:")
    print(code)
    
    refactored = apply_refactoring(code, smells, [0], MODEL, TEMP)
    
    print("\nRefactored code:")
    print(refactored)
    
    # Check that helper is inserted after __init__ or before process
    lines = refactored.split('\n')
    init_idx = None
    process_idx = None
    clean_idx = None
    
    for i, line in enumerate(lines):
        if '__init__' in line and 'def' in line:
            init_idx = i
        if 'def process' in line:
            process_idx = i
        if 'def _clean' in line:
            clean_idx = i
    
    print(f"\nMethod positions: __init__={init_idx}, process={process_idx}, _clean={clean_idx}")
    
    if clean_idx and init_idx and clean_idx > init_idx and clean_idx < process_idx:
        print("Helper insertion location: OK (after __init__, before process)")
    elif clean_idx and process_idx and clean_idx < process_idx:
        print("Helper insertion location: OK (before process)")
    else:
        print("Helper insertion location: WARNING (unexpected position)")
    
    return refactored


if __name__ == "__main__":
    print("Testing apply_refactoring directly...")
    print("Model:", MODEL)
    print("Temperature:", TEMP)
    print()
    
    test_apply_with_manual_smell()
    test_apply_single_helper_insertion()
    
    print("\n" + "=" * 70)
    print("Tests complete!")
    print("=" * 70)
