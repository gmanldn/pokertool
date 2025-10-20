#!/usr/bin/env python3
"""Test script to verify the refactored structure works correctly."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

print("=" * 60)
print("POKERTOOL STRUCTURE VERIFICATION TEST")
print("=" * 60)

tests_passed = 0
tests_failed = 0

def run_test(name, command, cwd=ROOT):
    """Run a test command and report results."""
    global tests_passed, tests_failed
    
    print(f"\n🧪 Test: {name}")
    print(f"   Command: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"   ✅ PASSED")
            tests_passed += 1
            return True
        else:
            print(f"   ❌ FAILED (exit code: {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            tests_failed += 1
            return False
    except subprocess.TimeoutExpired:
        print(f"   ❌ FAILED (timeout)")
        tests_failed += 1
        return False
    except Exception as e:
        print(f"   ❌ FAILED (exception: {e})")
        tests_failed += 1
        return False

# Test 1: Check structure
print("\n" + "=" * 60)
print("STRUCTURE VERIFICATION")
print("=" * 60)

pokertool_dir = ROOT / 'src' / 'pokertool'
nested_dir = pokertool_dir / 'pokertool'

if nested_dir.exists():
    print("❌ FAILED: Nested pokertool/pokertool directory still exists!")
    tests_failed += 1
else:
    print("✅ PASSED: No nested pokertool/pokertool directory")
    tests_passed += 1

required_files = ['__init__.py', '__main__.py', 'cli.py', 'core.py']
for filename in required_files:
    filepath = pokertool_dir / filename
    if filepath.exists():
        print(f"✅ PASSED: {filename} exists")
        tests_passed += 1
    else:
        print(f"❌ FAILED: {filename} missing")
        tests_failed += 1

# Test 2: Import tests
print("\n" + "=" * 60)
print("IMPORT TESTS")
print("=" * 60)

run_test(
    "Import pokertool module",
    "PYTHONPATH=./src .venv/bin/python -c 'import pokertool; print(pokertool.__version__)'"
)

run_test(
    "Import pokertool.core",
    "PYTHONPATH=./src .venv/bin/python -c 'from pokertool import core; print(\"OK\")'"
)

run_test(
    "Import pokertool.cli",
    "PYTHONPATH=./src .venv/bin/python -c 'from pokertool import cli; print(\"OK\")'"
)

# Test 3: Module execution
print("\n" + "=" * 60)
print("MODULE EXECUTION TESTS")
print("=" * 60)

run_test(
    "Run pokertool test mode",
    "PYTHONPATH=./src .venv/bin/python -m pokertool test"
)

# Test 4: Start script
print("\n" + "=" * 60)
print("START SCRIPT TEST")
print("=" * 60)

run_test(
    "Run start.py validation",
    "python3 start.py --validate"
)

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED! Structure refactoring successful!")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Please review.")
    sys.exit(1)
