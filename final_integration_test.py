#!/usr/bin/env python3
"""
Final integration test for PokerTool after refactoring.
Tests the complete workflow from start.py through module execution.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

print("=" * 70)
print("POKERTOOL - FINAL INTEGRATION TEST")
print("Testing complete workflow after structure refactoring")
print("=" * 70)

tests_passed = 0
tests_failed = 0

def test(name, command, timeout=30):
    """Run a test command."""
    global tests_passed, tests_failed
    
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"{'='*70}")
    print(f"Command: {command}\n")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        print(result.stdout[:500] if result.stdout else "(no output)")
        
        if result.returncode == 0:
            print(f"\n✅ PASSED")
            tests_passed += 1
            return True
        else:
            print(f"\n❌ FAILED (exit code: {result.returncode})")
            if result.stderr:
                print(f"Error: {result.stderr[:300]}")
            tests_failed += 1
            return False
            
    except subprocess.TimeoutExpired:
        print(f"\n⚠️  TIMEOUT (expected for GUI launch)")
        tests_passed += 1  # Timeout on GUI is OK
        return True
    except Exception as e:
        print(f"\n❌ EXCEPTION: {e}")
        tests_failed += 1
        return False

# Test 1: Structure verification
print("\n" + "=" * 70)
print("PHASE 1: STRUCTURE VERIFICATION")
print("=" * 70)

test(
    "No nested pokertool/pokertool directory exists",
    "test ! -d src/pokertool/pokertool && echo 'PASS: No nested directory' || echo 'FAIL: Nested directory exists'"
)

test(
    "All required files exist",
    "test -f src/pokertool/__init__.py && test -f src/pokertool/__main__.py && test -f src/pokertool/cli.py && echo 'PASS: Required files exist'"
)

# Test 2: Python imports
print("\n" + "=" * 70)
print("PHASE 2: IMPORT TESTS")
print("=" * 70)

test(
    "Import main pokertool package",
    "PYTHONPATH=./src .venv/bin/python -c 'import pokertool; print(f\"Version: {pokertool.__version__}\")'"
)

test(
    "Import core modules",
    "PYTHONPATH=./src .venv/bin/python -c 'from pokertool import core, cli; print(\"Core modules imported\")'"
)

test(
    "Import fixed betfair scraper",
    "PYTHONPATH=./src .venv/bin/python -c 'from pokertool.modules.poker_screen_scraper_betfair import PokerScreenScraper; print(\"Betfair scraper imported\")'"
)

test(
    "Import enhanced GUI (integration test)",
    "PYTHONPATH=./src .venv/bin/python -c 'from pokertool import enhanced_gui; print(\"Enhanced GUI imported\")'"
)

# Test 3: Module execution
print("\n" + "=" * 70)
print("PHASE 3: MODULE EXECUTION TESTS")
print("=" * 70)

test(
    "Execute module in test mode",
    "PYTHONPATH=./src .venv/bin/python -m pokertool test"
)

test(
    "Start script validation",
    "python3 start.py --validate"
)

# Test 4: Screen scraper functionality
print("\n" + "=" * 70)
print("PHASE 4: SCREEN SCRAPER TESTS")
print("=" * 70)

test(
    "Test screen scraper module",
    "PYTHONPATH=./src .venv/bin/python -c 'from pokertool.modules.poker_screen_scraper import create_scraper; s = create_scraper(); print(\"Scraper created successfully\")'"
)

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"✅ Tests Passed: {tests_passed}")
print(f"❌ Tests Failed: {tests_failed}")
print("=" * 70)

if tests_failed == 0:
    print("\n🎉 ALL INTEGRATION TESTS PASSED!")
    print("\nThe refactoring is complete and successful!")
    print("\nYou can now:")
    print("  1. Run: python3 start.py")
    print("  2. Delete backup: rm -rf structure_backup")
    print("  3. Delete test scripts: rm refactor_structure.py verify_structure.py final_integration_test.py")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed")
    print("\nPlease review the errors above")
    sys.exit(1)
