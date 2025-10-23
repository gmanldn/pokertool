#!/bin/bash
# Pre-commit hook for regression testing
# Install: ln -s ../../scripts/pre-commit-regression-check.sh .git/hooks/pre-commit

set -e

echo "🔍 Running pre-commit regression checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to repository root
cd "$(git rev-parse --show-toplevel)"

# Step 1: Run smoke tests (fast validation)
echo -e "${BLUE}1. Running smoke tests...${NC}"
if pytest -m smoke --timeout=60 -q --tb=line 2>&1 | tee /tmp/pokertool-smoke-tests.log; then
    echo -e "${GREEN}✅ Smoke tests passed${NC}"
else
    echo -e "${RED}❌ Smoke tests failed!${NC}"
    echo ""
    echo "Failed tests:"
    cat /tmp/pokertool-smoke-tests.log | grep FAILED || true
    echo ""
    echo "Commit aborted. Fix failing tests before committing."
    exit 1
fi

echo ""

# Step 2: Check test coverage for modified Python files
echo -e "${BLUE}2. Checking test coverage for modified files...${NC}"

# Get list of modified Python files in src/pokertool/
MODIFIED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '^src/pokertool/.*\.py$' || true)

if [ -n "$MODIFIED_PY_FILES" ]; then
    echo "Modified Python files:"
    echo "$MODIFIED_PY_FILES" | sed 's/^/  - /'
    echo ""

    MISSING_TESTS=""

    for FILE in $MODIFIED_PY_FILES; do
        # Skip __init__.py
        if [[ "$FILE" == *"__init__.py" ]]; then
            continue
        fi

        # Extract module name
        MODULE_NAME=$(basename "$FILE" .py)

        # Check if test file exists
        if ! find tests/ -name "test_${MODULE_NAME}.py" -print -quit | grep -q .; then
            MISSING_TESTS="${MISSING_TESTS}\n  - $FILE (no test_${MODULE_NAME}.py found)"
        fi
    done

    if [ -n "$MISSING_TESTS" ]; then
        echo -e "${YELLOW}⚠️  Warning: Modified files without tests:${NC}"
        echo -e "$MISSING_TESTS"
        echo ""
        echo -e "${YELLOW}Consider adding tests for these modules.${NC}"
        echo "Generate test skeleton with:"
        echo "  python scripts/generate_regression_tests.py --module <file>"
        echo ""

        # Ask user if they want to continue
        read -p "Continue with commit anyway? (y/N) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Commit aborted."
            exit 1
        fi
    else
        echo -e "${GREEN}✅ All modified modules have tests${NC}"
    fi
else
    echo "No Python files modified in src/pokertool/"
fi

echo ""

# Step 3: Run tests for modified modules
if [ -n "$MODIFIED_PY_FILES" ]; then
    echo -e "${BLUE}3. Running tests for modified modules...${NC}"

    TEST_FILES=""
    for FILE in $MODIFIED_PY_FILES; do
        MODULE_NAME=$(basename "$FILE" .py)
        TEST_FILE=$(find tests/ -name "test_${MODULE_NAME}.py" -print -quit)
        if [ -n "$TEST_FILE" ]; then
            TEST_FILES="${TEST_FILES} ${TEST_FILE}"
        fi
    done

    if [ -n "$TEST_FILES" ]; then
        echo "Running tests:"
        echo "$TEST_FILES" | tr ' ' '\n' | sed 's/^/  - /'
        echo ""

        if pytest $TEST_FILES -v --timeout=60 --tb=short; then
            echo -e "${GREEN}✅ Module tests passed${NC}"
        else
            echo -e "${RED}❌ Module tests failed!${NC}"
            echo ""
            echo "Commit aborted. Fix failing tests before committing."
            exit 1
        fi
    else
        echo "No test files found for modified modules"
    fi
else
    echo -e "${BLUE}3. Skipping module tests (no Python files modified)${NC}"
fi

echo ""

# Step 4: Check for test quality issues
echo -e "${BLUE}4. Checking test quality...${NC}"

# Check for tests without docstrings
MODIFIED_TEST_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '^tests/.*\.py$' || true)

if [ -n "$MODIFIED_TEST_FILES" ]; then
    echo "Modified test files:"
    echo "$MODIFIED_TEST_FILES" | sed 's/^/  - /'
    echo ""

    TESTS_WITHOUT_DOCS=""

    for TEST_FILE in $MODIFIED_TEST_FILES; do
        # Check for test functions without docstrings
        if grep -q "^def test_.*:" "$TEST_FILE"; then
            # This is a simplified check - could be enhanced
            UNDOCUMENTED=$(grep -A 1 "^def test_" "$TEST_FILE" | grep -v '"""' | grep "^def test_" || true)
            if [ -n "$UNDOCUMENTED" ]; then
                TESTS_WITHOUT_DOCS="${TESTS_WITHOUT_DOCS}\n  - $TEST_FILE"
            fi
        fi
    done

    if [ -n "$TESTS_WITHOUT_DOCS" ]; then
        echo -e "${YELLOW}⚠️  Warning: Test files may have undocumented tests:${NC}"
        echo -e "$TESTS_WITHOUT_DOCS"
        echo ""
        echo -e "${YELLOW}Add docstrings with version info (see REGRESSION_TESTING_STRATEGY.md)${NC}"
    else
        echo -e "${GREEN}✅ Test documentation looks good${NC}"
    fi
else
    echo "No test files modified"
fi

echo ""

# Final summary
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ All pre-commit checks passed!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Proceeding with commit..."

exit 0
