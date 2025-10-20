#!/bin/bash

# Error Summary and Analysis Tool
# Groups errors by type and shows frequency to identify critical issues

ERROR_LOG="/Users/georgeridout/Documents/github/pokertool/logs/errors-and-warnings.log"

if [ ! -f "$ERROR_LOG" ]; then
    echo "Error log not found. Run ./scripts/monitor-errors.sh first"
    exit 1
fi

echo "=========================================="
echo "Pokertool Error Summary"
echo "=========================================="
echo ""

# Count total errors and warnings
TOTAL_ERRORS=$(grep -c "ERROR" "$ERROR_LOG" || echo "0")
TOTAL_WARNINGS=$(grep -c "WARNING" "$ERROR_LOG" || echo "0")

echo "TOTAL: $TOTAL_ERRORS errors, $TOTAL_WARNINGS warnings"
echo ""
echo "=========================================="
echo "Top Recurring Errors (Grouped)"
echo "=========================================="

# Extract unique error messages and count occurrences
grep "ERROR" "$ERROR_LOG" | awk -F'|' '{print $NF}' | sort | uniq -c | sort -rn | head -10

echo ""
echo "=========================================="
echo "Top Recurring Warnings (Grouped)"
echo "=========================================="

grep "WARNING" "$ERROR_LOG" | awk -F'|' '{print $NF}' | sort | uniq -c | sort -rn | head -10

echo ""
echo "=========================================="
echo "Critical Issues to Fix"
echo "=========================================="

# Identify unique error types
echo ""
echo "1. Dependency Issues:"
grep -i "dependencies not available\|module named\|not installed" "$ERROR_LOG" | awk -F'|' '{print $NF}' | sort -u

echo ""
echo "2. Build/Compilation Errors:"
grep -i "error TS\|compilation\|build failed" "$ERROR_LOG" | head -5

echo ""
echo "=========================================="
echo ""
echo "For detailed log:"
echo "  cat $ERROR_LOG"
echo ""
echo "To monitor in real-time:"
echo "  tail -f $ERROR_LOG"
echo ""
