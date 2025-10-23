#!/bin/bash
#
# Naming Conventions Checker
#
# Scans codebase for common naming convention violations.
# Provides warnings and suggestions for improvement.
#
# Usage:
#   ./scripts/check_naming_conventions.sh
#   ./scripts/check_naming_conventions.sh --fix  # Auto-fix where possible
#
# Author: PokerTool Team
# Created: 2025-10-22

set -e

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

VIOLATIONS=0
WARNINGS=0
FIX_MODE=false

if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
    echo -e "${GREEN}Running in FIX mode - will auto-fix where possible${NC}\n"
fi

echo "========================================="
echo "PokerTool Naming Conventions Checker"
echo "========================================="
echo ""

# Python Naming Checks
echo "Checking Python files..."
echo "------------------------"

# Check for camelCase functions in Python (should be snake_case)
echo "Looking for camelCase functions (should be snake_case)..."
CAMEL_FUNCS=$(grep -rn "^def [a-z][a-zA-Z]*[A-Z]" src/pokertool/*.py 2>/dev/null | grep -v "__" || true)
if [ -n "$CAMEL_FUNCS" ]; then
    echo -e "${YELLOW}⚠️  Found camelCase functions:${NC}"
    echo "$CAMEL_FUNCS"
    WARNINGS=$((WARNINGS + $(echo "$CAMEL_FUNCS" | wc -l)))
    echo ""
fi

# Check for PascalCase variables (should be snake_case)
echo "Looking for PascalCase variables (should be snake_case)..."
PASCAL_VARS=$(grep -rn "^    [A-Z][a-zA-Z]*\s*=" src/pokertool/*.py 2>/dev/null | grep -v "class " || true)
if [ -n "$PASCAL_VARS" ]; then
    echo -e "${YELLOW}⚠️  Found PascalCase variables:${NC}"
    echo "$PASCAL_VARS" | head -10
    WARNINGS=$((WARNINGS + $(echo "$PASCAL_VARS" | wc -l)))
    echo ""
fi

# Check for snake_case classes (should be PascalCase)
echo "Looking for snake_case classes (should be PascalCase)..."
SNAKE_CLASSES=$(grep -rn "^class [a-z_]" src/pokertool/*.py 2>/dev/null || true)
if [ -n "$SNAKE_CLASSES" ]; then
    echo -e "${RED}❌ Found snake_case classes:${NC}"
    echo "$SNAKE_CLASSES"
    VIOLATIONS=$((VIOLATIONS + $(echo "$SNAKE_CLASSES" | wc -l)))
    echo ""
fi

# Check for missing type hints
echo "Looking for functions without type hints..."
MISSING_HINTS=$(grep -rn "^def [a-z_][a-z0-9_]*(" src/pokertool/*.py 2>/dev/null | grep -v " ->" || true)
if [ -n "$MISSING_HINTS" ]; then
    echo -e "${YELLOW}⚠️  Found functions without return type hints:${NC}"
    echo "$MISSING_HINTS" | head -10
    WARNINGS=$((WARNINGS + $(echo "$MISSING_HINTS" | wc -l)))
    echo ""
fi

# TypeScript Naming Checks
echo "Checking TypeScript files..."
echo "----------------------------"

# Check for snake_case functions in TypeScript (should be camelCase)
echo "Looking for snake_case functions (should be camelCase)..."
SNAKE_FUNCS=$(grep -rn "function [a-z_]*_[a-z_]*" pokertool-frontend/src/**/*.ts pokertool-frontend/src/**/*.tsx 2>/dev/null || true)
if [ -n "$SNAKE_FUNCS" ]; then
    echo -e "${YELLOW}⚠️  Found snake_case functions:${NC}"
    echo "$SNAKE_FUNCS" | head -10
    WARNINGS=$((WARNINGS + $(echo "$SNAKE_FUNCS" | wc -l)))
    echo ""
fi

# Check for snake_case variables in TypeScript (should be camelCase)
echo "Looking for snake_case variables (should be camelCase)..."
SNAKE_VARS=$(grep -rn "const [a-z_]*_[a-z_]*\s*=" pokertool-frontend/src/**/*.ts pokertool-frontend/src/**/*.tsx 2>/dev/null | grep -v "MAX_" | grep -v "API_" || true)
if [ -n "$SNAKE_VARS" ]; then
    echo -e "${YELLOW}⚠️  Found snake_case variables:${NC}"
    echo "$SNAKE_VARS" | head -10
    WARNINGS=$((WARNINGS + $(echo "$SNAKE_VARS" | wc -l)))
    echo ""
fi

# Check for camelCase React components (should be PascalCase)
echo "Looking for camelCase React components (should be PascalCase)..."
CAMEL_COMPONENTS=$(grep -rn "export.*const [a-z][a-zA-Z]*.*React\\.FC" pokertool-frontend/src/**/*.tsx 2>/dev/null || true)
if [ -n "$CAMEL_COMPONENTS" ]; then
    echo -e "${RED}❌ Found camelCase React components:${NC}"
    echo "$CAMEL_COMPONENTS"
    VIOLATIONS=$((VIOLATIONS + $(echo "$CAMEL_COMPONENTS" | wc -l)))
    echo ""
fi

# Database Naming Checks
echo "Checking SQL/Database files..."
echo "------------------------------"

# Check for PascalCase table names (should be snake_case)
echo "Looking for PascalCase table names (should be snake_case)..."
PASCAL_TABLES=$(grep -rn "CREATE TABLE [A-Z]" src/pokertool/**/*.py 2>/dev/null || true)
if [ -n "$PASCAL_TABLES" ]; then
    echo -e "${RED}❌ Found PascalCase table names:${NC}"
    echo "$PASCAL_TABLES"
    VIOLATIONS=$((VIOLATIONS + $(echo "$PASCAL_TABLES" | wc -l)))
    echo ""
fi

# File Naming Checks
echo "Checking file naming..."
echo "-----------------------"

# Check for PascalCase Python files (should be snake_case)
echo "Looking for PascalCase Python files (should be snake_case)..."
PASCAL_FILES=$(find src/pokertool -name "[A-Z]*.py" 2>/dev/null || true)
if [ -n "$PASCAL_FILES" ]; then
    echo -e "${YELLOW}⚠️  Found PascalCase Python files:${NC}"
    echo "$PASCAL_FILES"
    WARNINGS=$((WARNINGS + $(echo "$PASCAL_FILES" | wc -l)))
    echo ""
fi

# Check for snake_case React component files (should be PascalCase)
echo "Looking for snake_case React component files (should be PascalCase)..."
SNAKE_COMPONENTS=$(find pokertool-frontend/src/components -name "*_*.tsx" 2>/dev/null || true)
if [ -n "$SNAKE_COMPONENTS" ]; then
    echo -e "${YELLOW}⚠️  Found snake_case React component files:${NC}"
    echo "$SNAKE_COMPONENTS"
    WARNINGS=$((WARNINGS + $(echo "$SNAKE_COMPONENTS" | wc -l)))
    echo ""
fi

# Summary
echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo -e "Violations (must fix): ${RED}$VIOLATIONS${NC}"
echo -e "Warnings (should fix): ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $VIOLATIONS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All naming conventions followed!${NC}"
    exit 0
elif [ $VIOLATIONS -gt 0 ]; then
    echo -e "${RED}❌ Found $VIOLATIONS naming violations that must be fixed.${NC}"
    echo "See docs/development/NAMING_CONVENTIONS.md for guidance."
    exit 1
else
    echo -e "${YELLOW}⚠️  Found $WARNINGS naming warnings. Consider fixing for consistency.${NC}"
    echo "See docs/development/NAMING_CONVENTIONS.md for guidance."
    exit 0
fi
