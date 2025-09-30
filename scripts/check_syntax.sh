#!/bin/bash
# PokerTool Syntax Check and Validation Script
# Version: 1.0
# Date: 2025-09-29

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     PokerTool Syntax Check & Validation                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
PASSED=0
FAILED=0

# Function to check Python syntax
check_syntax() {
    local file=$1
    TOTAL=$((TOTAL + 1))
    
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $file"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $file"
        python3 -m py_compile "$file" 2>&1 | head -3
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Main Python source files
echo "📝 Checking main source files..."
echo "─────────────────────────────────────────────────────────"

MAIN_FILES=(
    "src/pokertool/__init__.py"
    "src/pokertool/core.py"
    "src/pokertool/api.py"
    "src/pokertool/bankroll_management.py"
    "src/pokertool/cli.py"
    "src/pokertool/compliance.py"
    "src/pokertool/database.py"
    "src/pokertool/enhanced_gui.py"
    "src/pokertool/error_handling.py"
    "src/pokertool/game_selection.py"
    "src/pokertool/gto_solver.py"
    "src/pokertool/gui.py"
    "src/pokertool/hud_overlay.py"
    "src/pokertool/ml_opponent_modeling.py"
    "src/pokertool/multi_table_support.py"
    "src/pokertool/ocr_recognition.py"
    "src/pokertool/production_database.py"
    "src/pokertool/scrape.py"
    "src/pokertool/storage.py"
    "src/pokertool/threading.py"
    "src/pokertool/tournament_support.py"
    "src/pokertool/variance_calculator.py"
)

for file in "${MAIN_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_syntax "$file"
    else
        echo -e "${YELLOW}⚠${NC} $file (not found)"
    fi
done

echo ""

# Test files
echo "🧪 Checking test files..."
echo "─────────────────────────────────────────────────────────"

if [ -d "tests" ]; then
    for file in tests/test_*.py; do
        if [ -f "$file" ]; then
            check_syntax "$file"
        fi
    done
else
    echo -e "${YELLOW}⚠${NC} tests directory not found"
fi

echo ""

# Root level Python files
echo "📦 Checking root level files..."
echo "─────────────────────────────────────────────────────────"

ROOT_FILES=(
    "start.py"
    "poker_test.py"
    "enhanced_tests.py"
    "autoconfirm.py"
    "logger.py"
)

for file in "${ROOT_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_syntax "$file"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "                    VALIDATION SUMMARY"
echo "════════════════════════════════════════════════════════════"
echo "Total files checked: $TOTAL"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All files passed syntax validation!${NC}"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}✗ $FAILED file(s) failed syntax validation${NC}"
    echo ""
    exit 1
fi
