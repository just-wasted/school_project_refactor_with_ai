#!/usr/bin/env python3
"""Test accepting only first smell from service.py (multiple smells)."""

import os
import sys

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

def main():
    print("=" * 70)
    print("TEST: service.py - Accept FIRST smell only")
    print("=" * 70)
    
    # Read original code
    with open('code_smells/service.py', 'r') as f:
        original_code = f.read()
    
    print(f"Original code length: {len(original_code)} chars")
    print(f"Original code lines: {len(original_code.splitlines())} lines")
    
    # Analyze
    print("\nAnalyzing...")
    all_smells = []
    for st in SMELL_TYPES:
        try:
            result = call_ollama(original_code, MODEL, TEMP, mode="analyze", smell_type=st)
            smells = extract_smells(result, original_code)
            all_smells.extend(smells)
        except Exception as e:
            print(f"Error analyzing {st}: {e}")
    
    all_smells = deduplicate_smells(all_smells)
    print(f"Found {len(all_smells)} unique smell(s)")
    
    if len(all_smells) == 0:
        print("No smells found - test skipped")
        return
    
    # Show all smells
    for i, s in enumerate(all_smells):
        loc = s.get('location', {})
        print(f"  {i+1}. {s.get('type', 'unknown')} at lines {loc.get('start_line', '?')}-{loc.get('end_line', '?')}")
    
    # Select ONLY the first smell
    selected = [0]
    first_smell = all_smells[0]
    
    print(f"\nApplying ONLY smell 1: {first_smell.get('type', 'unknown')}")
    
    # Apply
    refactored_code = apply_refactoring(original_code, all_smells, selected, MODEL, TEMP)
    
    print(f"\nRefactored code length: {len(refactored_code)} chars")
    print(f"Refactored code lines: {len(refactored_code.splitlines())} lines")
    
    # Save to file for inspection
    with open('/tmp/refactored_service_first.py', 'w') as f:
        f.write(refactored_code)
    print(f"\nRefactored code saved to: /tmp/refactored_service_first.py")
    
    # Verify
    print("\nVerification:")
    
    # Syntax check
    ok, err = verify_syntax(refactored_code)
    print(f"- Syntax: {'OK' if ok else 'FAILED: ' + err}")
    
    # Pyflakes check
    ok2, err2 = run_pyflakes(refactored_code)
    print(f"- Pyflakes: {'OK' if ok2 else 'FAILED: ' + err2}")
    
    # Check that first smell's old code was removed
    old_code = first_smell.get('old_code', '')
    if old_code and old_code.strip() in refactored_code:
        print(f"- First smell old code removed: FAILED (still present)")
    else:
        print(f"- First smell old code removed: OK")
    
    # Check that first smell's new code was added
    new_code = first_smell.get('new_code', '')
    if new_code and new_code.strip() in refactored_code:
        print(f"- First smell new code added: OK")
    else:
        print(f"- First smell new code added: FAILED")
    
    # Check that OTHER smells' old code is STILL PRESENT (not applied)
    other_smells_present = []
    other_smells_removed = []
    for i, s in enumerate(all_smells[1:], start=2):
        old = s.get('old_code', '')
        if old and old.strip() in refactored_code:
            other_smells_present.append(i)
        else:
            other_smells_removed.append(i)
    
    print(f"- Other smells still present (not applied): {len(other_smells_present)} of {len(all_smells)-1}")
    if other_smells_removed:
        print(f"  WARNING: Smells removed but not selected: {other_smells_removed}")
    
    # Show first 60 lines of refactored code
    print("\nFirst 60 lines of refactored code:")
    print("-" * 70)
    lines = refactored_code.split('\n')
    for i, line in enumerate(lines[:60], 1):
        print(f"{i:3}: {line}")
    if len(lines) > 60:
        print(f"... ({len(lines) - 60} more lines)")
    print("-" * 70)

if __name__ == "__main__":
    main()
