#!/usr/bin/env python3
"""Test script for apply prompt improvements."""

import os
import sys
import subprocess
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from refactoring_agent import (
    analyze_file_for_smells,
    apply_refactoring,
    verify_syntax,
    run_pyflakes,
    deduplicate_smells,
    extract_smells,
    call_ollama,
)

MODEL = "gemma4:e2b"
TEMP = 0.1

def test_duplicate_code_single_smell():
    """Test Duplicate Code refactoring on data_cleaner.py - single smell, accept it."""
    print("=" * 70)
    print("TEST 1: Duplicate Code - data_cleaner.py (single smell)")
    print("=" * 70)
    
    code_file = "code_smells/data_cleaner.py"
    with open(code_file, 'r') as f:
        original_code = f.read()
    
    print("Original code:")
    print("-" * 70)
    print(original_code)
    print("-" * 70)
    
    # Analyze
    from refactoring_agent import SMELL_TYPES, SYSTEM_PROMPT_ANALYZE
    all_smells = []
    for st in SMELL_TYPES:
        try:
            result = call_ollama(original_code, MODEL, TEMP, mode="analyze", smell_type=st)
            smells = extract_smells(result, original_code)
            all_smells.extend(smells)
        except Exception as e:
            print(f"Error analyzing {st}: {e}")
    
    all_smells = deduplicate_smells(all_smells)
    print(f"\nFound {len(all_smells)} smell(s)")
    
    if not all_smells:
        print("No smells found - skipping test")
        return None
    
    # Select first smell
    selected = [0]
    
    # Apply
    print("\nApplying refactoring...")
    refactored_code = apply_refactoring(original_code, all_smells, selected, MODEL, TEMP)
    
    print("\nRefactored code:")
    print("-" * 70)
    print(refactored_code)
    print("-" * 70)
    
    # Verify
    print("\nVerification:")
    print(f"- Code length: {len(original_code)} -> {len(refactored_code)} chars")
    
    # Check syntax
    ok, err = verify_syntax(refactored_code)
    print(f"- Syntax: {'OK' if ok else 'FAILED: ' + err}")
    
    # Check pyflakes
    ok2, err2 = run_pyflakes(refactored_code)
    print(f"- Pyflakes: {'OK' if ok2 else 'FAILED: ' + err2}")
    
    # Check if old code was removed
    smell = all_smells[0]
    old_code = smell.get('old_code', '')
    if old_code and old_code.strip() in refactored_code:
        print(f"- Old code removal: FAILED (old code still present)")
    else:
        print(f"- Old code removal: OK")
    
    # Check if new code was added
    new_code = smell.get('new_code', '')
    if new_code and new_code.strip() in refactored_code:
        print(f"- New code insertion: OK")
    else:
        print(f"- New code insertion: FAILED")
    
    return refactored_code


def test_long_method_first_accept():
    """Test Long Method on service.py - accept only first smell."""
    print("\n" + "=" * 70)
    print("TEST 2: Long Method - service.py (accept first smell only)")
    print("=" * 70)
    
    code_file = "code_smells/service.py"
    with open(code_file, 'r') as f:
        original_code = f.read()
    
    # Analyze
    from refactoring_agent import SMELL_TYPES, SYSTEM_PROMPT_ANALYZE
    all_smells = []
    for st in SMELL_TYPES:
        try:
            result = call_ollama(original_code, MODEL, TEMP, mode="analyze", smell_type=st)
            smells = extract_smells(result, original_code)
            all_smells.extend(smells)
        except Exception as e:
            print(f"Error analyzing {st}: {e}")
    
    all_smells = deduplicate_smells(all_smells)
    print(f"\nFound {len(all_smells)} smell(s)")
    
    if not all_smells:
        print("No smells found - skipping test")
        return None
    
    # Select only first smell
    selected = [0]
    
    # Apply
    print(f"\nApplying first smell only: {all_smells[0].get('type', 'unknown')}")
    refactored_code = apply_refactoring(original_code, all_smells, selected, MODEL, TEMP)
    
    print("\nRefactored code (first 50 lines):")
    print("-" * 70)
    lines = refactored_code.split('\n')
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3}: {line}")
    if len(lines) > 50:
        print(f"... ({len(lines) - 50} more lines)")
    print("-" * 70)
    
    # Verify
    print("\nVerification:")
    
    # Check syntax
    ok, err = verify_syntax(refactored_code)
    print(f"- Syntax: {'OK' if ok else 'FAILED: ' + err}")
    
    # Check pyflakes
    ok2, err2 = run_pyflakes(refactored_code)
    print(f"- Pyflakes: {'OK' if ok2 else 'FAILED: ' + err2}")
    
    # Check that only the first smell was applied
    smell = all_smells[0]
    old_code = smell.get('old_code', '')
    if old_code and old_code.strip() in refactored_code:
        print(f"- Old code removal (first smell): FAILED")
    else:
        print(f"- Old code removal (first smell): OK")
    
    new_code = smell.get('new_code', '')
    if new_code and new_code.strip() in refactored_code:
        print(f"- New code insertion (first smell): OK")
    else:
        print(f"- New code insertion (first smell): FAILED")
    
    # Check that other smells were NOT applied
    if len(all_smells) > 1:
        other_smell = all_smells[1]
        other_old = other_smell.get('old_code', '')
        if other_old and other_old.strip() in refactored_code:
            print(f"- Other smells NOT applied: OK (old code still present)")
        else:
            print(f"- Other smells NOT applied: WARNING (old code removed but not selected)")
    
    return refactored_code


def test_long_method_middle_accept():
    """Test Long Method on service.py - accept middle smell."""
    print("\n" + "=" * 70)
    print("TEST 3: Long Method - service.py (accept middle smell)")
    print("=" * 70)
    
    code_file = "code_smells/service.py"
    with open(code_file, 'r') as f:
        original_code = f.read()
    
    # Analyze
    from refactoring_agent import SMELL_TYPES, SYSTEM_PROMPT_ANALYZE
    all_smells = []
    for st in SMELL_TYPES:
        try:
            result = call_ollama(original_code, MODEL, TEMP, mode="analyze", smell_type=st)
            smells = extract_smells(result, original_code)
            all_smells.extend(smells)
        except Exception as e:
            print(f"Error analyzing {st}: {e}")
    
    all_smells = deduplicate_smells(all_smells)
    print(f"\nFound {len(all_smells)} smell(s)")
    
    if len(all_smells) < 2:
        print("Need at least 2 smells for middle test - skipping")
        return None
    
    # Select middle smell
    mid_index = len(all_smells) // 2
    selected = [mid_index]
    
    # Apply
    print(f"\nApplying middle smell ({mid_index+1}/{len(all_smells)}): {all_smells[mid_index].get('type', 'unknown')}")
    refactored_code = apply_refactoring(original_code, all_smells, selected, MODEL, TEMP)
    
    print("\nRefactored code (relevant section):")
    print("-" * 70)
    lines = refactored_code.split('\n')
    smell = all_smells[mid_index]
    loc = smell.get('location', {})
    start = loc.get('start_line', 0) - 2
    end = loc.get('end_line', 0) + 5
    for i, line in enumerate(lines[max(0, start):min(len(lines), end)], start=max(0, start)+1):
        print(f"{i:3}: {line}")
    print("-" * 70)
    
    # Verify
    print("\nVerification:")
    
    # Check syntax
    ok, err = verify_syntax(refactored_code)
    print(f"- Syntax: {'OK' if ok else 'FAILED: ' + err}")
    
    # Check pyflakes
    ok2, err2 = run_pyflakes(refactored_code)
    print(f"- Pyflakes: {'OK' if ok2 else 'FAILED: ' + err2}")
    
    # Check that selected smell was applied
    old_code = smell.get('old_code', '')
    if old_code and old_code.strip() in refactored_code:
        print(f"- Selected old code removal: FAILED")
    else:
        print(f"- Selected old code removal: OK")
    
    new_code = smell.get('new_code', '')
    if new_code and new_code.strip() in refactored_code:
        print(f"- Selected new code insertion: OK")
    else:
        print(f"- Selected new code insertion: FAILED")
    
    return refactored_code


def test_long_method_last_accept():
    """Test Long Method on service.py - accept last smell."""
    print("\n" + "=" * 70)
    print("TEST 4: Long Method - service.py (accept last smell)")
    print("=" * 70)
    
    code_file = "code_smells/service.py"
    with open(code_file, 'r') as f:
        original_code = f.read()
    
    # Analyze
    from refactoring_agent import SMELL_TYPES, SYSTEM_PROMPT_ANALYZE
    all_smells = []
    for st in SMELL_TYPES:
        try:
            result = call_ollama(original_code, MODEL, TEMP, mode="analyze", smell_type=st)
            smells = extract_smells(result, original_code)
            all_smells.extend(smells)
        except Exception as e:
            print(f"Error analyzing {st}: {e}")
    
    all_smells = deduplicate_smells(all_smells)
    print(f"\nFound {len(all_smells)} smell(s)")
    
    if not all_smells:
        print("No smells found - skipping test")
        return None
    
    # Select last smell
    selected = [len(all_smells) - 1]
    
    # Apply
    print(f"\nApplying last smell ({len(all_smells)}/{len(all_smells)}): {all_smells[-1].get('type', 'unknown')}")
    refactored_code = apply_refactoring(original_code, all_smells, selected, MODEL, TEMP)
    
    print("\nRefactored code (last 30 lines):")
    print("-" * 70)
    lines = refactored_code.split('\n')
    for i, line in enumerate(lines[-30:], start=len(lines)-29):
        print(f"{i:3}: {line}")
    print("-" * 70)
    
    # Verify
    print("\nVerification:")
    
    # Check syntax
    ok, err = verify_syntax(refactored_code)
    print(f"- Syntax: {'OK' if ok else 'FAILED: ' + err}")
    
    # Check pyflakes
    ok2, err2 = run_pyflakes(refactored_code)
    print(f"- Pyflakes: {'OK' if ok2 else 'FAILED: ' + err2}")
    
    # Check that selected smell was applied
    smell = all_smells[-1]
    old_code = smell.get('old_code', '')
    if old_code and old_code.strip() in refactored_code:
        print(f"- Selected old code removal: FAILED")
    else:
        print(f"- Selected old code removal: OK")
    
    new_code = smell.get('new_code', '')
    if new_code and new_code.strip() in refactored_code:
        print(f"- Selected new code insertion: OK")
    else:
        print(f"- Selected new code insertion: FAILED")
    
    # Check that other smells were NOT applied
    if len(all_smells) > 1:
        other_smell = all_smells[0]
        other_old = other_smell.get('old_code', '')
        if other_old and other_old.strip() in refactored_code:
            print(f"- Other smells NOT applied: OK (old code still present)")
        else:
            print(f"- Other smells NOT applied: WARNING (old code removed but not selected)")
    
    return refactored_code


if __name__ == "__main__":
    print("Testing apply prompt improvements...")
    print("Model:", MODEL)
    print("Temperature:", TEMP)
    print()
    
    # Run tests
    test_duplicate_code_single_smell()
    test_long_method_first_accept()
    test_long_method_middle_accept()
    test_long_method_last_accept()
    
    print("\n" + "=" * 70)
    print("Tests complete!")
    print("=" * 70)
