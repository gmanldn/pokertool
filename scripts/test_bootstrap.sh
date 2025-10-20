#!/bin/bash
# test_bootstrap.sh - Test the bootstrap scripts without actually installing anything

echo "=================================="
echo "Bootstrap Script Test Suite"
echo "=================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

tests_passed=0
tests_failed=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓ PASS${NC}: $2"
        ((tests_passed++))
    else
        echo -e "${RED}✗ FAIL${NC}: $2"
        ((tests_failed++))
    fi
}

echo "Testing Bootstrap Scripts..."
echo ""

# Test 1: Check scripts exist
echo "Test 1: Checking bootstrap scripts exist..."
if [ -f "first_run_mac.sh" ] && [ -f "first_run_linux.sh" ] && [ -f "first_run_windows.ps1" ]; then
    test_result 0 "All bootstrap scripts exist"
else
    test_result 1 "Missing bootstrap scripts"
fi

# Test 2: Check scripts are executable (Unix)
echo "Test 2: Checking Unix scripts are executable..."
if [ -x "first_run_mac.sh" ] && [ -x "first_run_linux.sh" ]; then
    test_result 0 "Unix scripts are executable"
else
    test_result 1 "Unix scripts are not executable"
fi

# Test 3: Check for start.py
echo "Test 3: Checking start.py exists..."
if [ -f "start.py" ]; then
    test_result 0 "start.py exists"
else
    test_result 1 "start.py not found"
fi

# Test 4: Check requirements.txt
echo "Test 4: Checking requirements.txt exists..."
if [ -f "requirements.txt" ]; then
    test_result 0 "requirements.txt exists"
else
    test_result 1 "requirements.txt not found"
fi

# Test 5: Validate macOS script syntax
echo "Test 5: Validating macOS script syntax..."
if bash -n first_run_mac.sh 2>/dev/null; then
    test_result 0 "macOS script syntax valid"
else
    test_result 1 "macOS script has syntax errors"
fi

# Test 6: Validate Linux script syntax
echo "Test 6: Validating Linux script syntax..."
if bash -n first_run_linux.sh 2>/dev/null; then
    test_result 0 "Linux script syntax valid"
else
    test_result 1 "Linux script has syntax errors"
fi

# Test 7: Check Python detection logic in scripts
echo "Test 7: Checking Python detection logic..."
if grep -q "command -v python3" first_run_mac.sh && grep -q "command -v python3" first_run_linux.sh; then
    test_result 0 "Python detection logic present"
else
    test_result 1 "Python detection logic missing"
fi

# Test 8: Check for proper error handling
echo "Test 8: Checking error handling..."
if grep -q "set -e" first_run_mac.sh && grep -q "set -e" first_run_linux.sh; then
    test_result 0 "Error handling (set -e) present"
else
    test_result 1 "Error handling missing"
fi

# Test 9: Check for logging functions
echo "Test 9: Checking logging functions..."
if grep -q "log_info" first_run_mac.sh && grep -q "log_error" first_run_mac.sh; then
    test_result 0 "Logging functions present"
else
    test_result 1 "Logging functions missing"
fi

# Test 10: Check FIRST_RUN_GUIDE exists
echo "Test 10: Checking FIRST_RUN_GUIDE.md exists..."
if [ -f "FIRST_RUN_GUIDE.md" ]; then
    test_result 0 "FIRST_RUN_GUIDE.md exists"
else
    test_result 1 "FIRST_RUN_GUIDE.md not found"
fi

# Test 11: Verify current Python installation
echo "Test 11: Verifying current Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
        test_result 0 "Python $PYTHON_VERSION installed (>= 3.8)"
    else
        test_result 1 "Python $PYTHON_VERSION too old (need >= 3.8)"
    fi
else
    test_result 1 "Python 3 not found"
fi

# Test 12: Check if start.py is valid Python
echo "Test 12: Validating start.py syntax..."
if python3 -m py_compile start.py 2>/dev/null; then
    test_result 0 "start.py has valid Python syntax"
else
    test_result 1 "start.py has syntax errors"
fi

# Summary
echo ""
echo "=================================="
echo "Test Summary"
echo "=================================="
echo -e "Passed: ${GREEN}$tests_passed${NC}"
echo -e "Failed: ${RED}$tests_failed${NC}"
echo "=================================="

if [ $tests_failed -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Bootstrap scripts are ready to use:"
    echo "  macOS:   ./first_run_mac.sh"
    echo "  Linux:   ./first_run_linux.sh"
    echo "  Windows: .\\first_run_windows.ps1"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
