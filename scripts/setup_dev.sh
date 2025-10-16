#!/usr/bin/env bash
#
# PokerTool Development Environment Setup Script
# ==============================================
#
# Automatically sets up a complete development environment for PokerTool
# Supports macOS, Linux, and Windows (via Git Bash/WSL)
#
# Usage:
#   ./scripts/setup_dev.sh              # Full setup
#   ./scripts/setup_dev.sh --quick      # Skip optional tools
#   ./scripts/setup_dev.sh --help       # Show help
#
# Version: 86.5.0
# Author: PokerTool Development Team

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.10"
NODE_MIN_VERSION="16"
QUICK_MODE=false

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Compare version numbers
version_ge() {
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
}

# ============================================================================
# Usage Information
# ============================================================================

show_help() {
    cat << EOF
PokerTool Development Environment Setup

Usage: $0 [OPTIONS]

Options:
    --quick         Skip optional tools (Tesseract, PostgreSQL)
    --help          Show this help message

This script will:
    1. Detect your operating system
    2. Check Python and Node.js versions
    3. Create Python virtual environment
    4. Install Python dependencies
    5. Install Node.js dependencies (frontend)
    6. Install Tesseract OCR (optional)
    7. Set up PostgreSQL (optional)
    8. Configure pre-commit hooks
    9. Create .env files
    10. Run initial tests

Supported platforms:
    - macOS (via Homebrew)
    - Ubuntu/Debian Linux (via apt)
    - Other Linux (manual instructions provided)
    - Windows (via Git Bash or WSL)

EOF
    exit 0
}

# ============================================================================
# Parse Arguments
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ============================================================================
# Welcome Message
# ============================================================================

print_header "PokerTool Development Setup v86.5.0"
echo "This script will set up your development environment."
echo "Estimated time: 5-10 minutes"
echo ""

if [ "$QUICK_MODE" = true ]; then
    print_info "Quick mode enabled - skipping optional tools"
fi

# ============================================================================
# Detect Operating System
# ============================================================================

print_header "Step 1: Detecting Operating System"

OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    print_success "Detected: macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if [ -f /etc/debian_version ]; then
        OS="debian"
        print_success "Detected: Debian/Ubuntu Linux"
    else
        print_success "Detected: Linux"
    fi
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
    print_success "Detected: Windows (Git Bash/Cygwin)"
else
    print_warning "Unknown OS: $OSTYPE"
fi

# ============================================================================
# Check Python
# ============================================================================

print_header "Step 2: Checking Python"

if ! command_exists python3; then
    print_error "Python 3 not found!"
    echo "Please install Python $PYTHON_MIN_VERSION or higher:"
    echo "  macOS:   brew install python@3.13"
    echo "  Ubuntu:  sudo apt install python3 python3-pip python3-venv"
    echo "  Windows: Download from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Found Python $PYTHON_VERSION"

# Check version
if ! version_ge "$PYTHON_VERSION" "$PYTHON_MIN_VERSION"; then
    print_error "Python $PYTHON_MIN_VERSION or higher required (found $PYTHON_VERSION)"
    exit 1
fi

# ============================================================================
# Check Node.js (for frontend)
# ============================================================================

print_header "Step 3: Checking Node.js"

if ! command_exists node; then
    print_warning "Node.js not found - required for frontend development"
    echo "Install Node.js:"
    echo "  macOS:   brew install node"
    echo "  Ubuntu:  sudo apt install nodejs npm"
    echo "  Windows: Download from https://nodejs.org/"
    if [ "$QUICK_MODE" = false ]; then
        read -p "Continue without Node.js? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    print_success "Found Node.js v$NODE_VERSION"

    if ! version_ge "$NODE_VERSION" "$NODE_MIN_VERSION"; then
        print_warning "Node.js $NODE_MIN_VERSION or higher recommended (found $NODE_VERSION)"
    fi
fi

# ============================================================================
# Create Python Virtual Environment
# ============================================================================

print_header "Step 4: Setting up Python Virtual Environment"

if [ -d ".venv" ]; then
    print_info "Virtual environment already exists"
    read -p "Recreate? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing virtual environment..."
        rm -rf .venv
    fi
fi

if [ ! -d ".venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source .venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
python -m pip install --upgrade pip --quiet
print_success "pip upgraded"

# ============================================================================
# Install Python Dependencies
# ============================================================================

print_header "Step 5: Installing Python Dependencies"

if [ -f "requirements.txt" ]; then
    print_info "Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found!"
    exit 1
fi

# Install development dependencies if available
if [ -f "requirements-dev.txt" ]; then
    print_info "Installing development dependencies..."
    pip install -r requirements-dev.txt
    print_success "Development dependencies installed"
fi

# ============================================================================
# Install Node.js Dependencies (Frontend)
# ============================================================================

if command_exists node && [ -d "pokertool-frontend" ]; then
    print_header "Step 6: Installing Frontend Dependencies"

    cd pokertool-frontend

    if [ -f "package.json" ]; then
        print_info "Installing Node.js packages..."
        npm install
        print_success "Frontend dependencies installed"
    else
        print_warning "package.json not found in pokertool-frontend/"
    fi

    cd ..
else
    print_header "Step 6: Skipping Frontend Setup"
    print_warning "Node.js not available or pokertool-frontend/ not found"
fi

# ============================================================================
# Install Tesseract OCR (Optional)
# ============================================================================

if [ "$QUICK_MODE" = false ]; then
    print_header "Step 7: Installing Tesseract OCR (Optional)"

    if command_exists tesseract; then
        TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1 | cut -d' ' -f2)
        print_success "Tesseract already installed (v$TESSERACT_VERSION)"
    else
        print_info "Tesseract not found. Install for OCR functionality."

        case $OS in
            macos)
                if command_exists brew; then
                    read -p "Install Tesseract via Homebrew? (y/n) " -n 1 -r
                    echo
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        brew install tesseract
                        print_success "Tesseract installed"
                    fi
                else
                    print_warning "Homebrew not found. Install from: https://brew.sh/"
                fi
                ;;
            debian)
                print_info "Install with: sudo apt install tesseract-ocr"
                ;;
            *)
                print_info "Visit: https://github.com/tesseract-ocr/tesseract"
                ;;
        esac
    fi
else
    print_header "Step 7: Skipping Tesseract OCR (Quick Mode)"
fi

# ============================================================================
# PostgreSQL Setup (Optional)
# ============================================================================

if [ "$QUICK_MODE" = false ]; then
    print_header "Step 8: PostgreSQL Setup (Optional)"

    if command_exists psql; then
        print_success "PostgreSQL already installed"
    else
        print_info "PostgreSQL not found (optional - SQLite will be used by default)"

        case $OS in
            macos)
                if command_exists brew; then
                    print_info "Install with: brew install postgresql@15"
                fi
                ;;
            debian)
                print_info "Install with: sudo apt install postgresql postgresql-contrib"
                ;;
            *)
                print_info "Visit: https://www.postgresql.org/download/"
                ;;
        esac
    fi
else
    print_header "Step 8: Skipping PostgreSQL (Quick Mode)"
fi

# ============================================================================
# Configure Pre-commit Hooks
# ============================================================================

print_header "Step 9: Configuring Pre-commit Hooks"

if [ -f ".pre-commit-config.yaml" ]; then
    print_info "Installing pre-commit hooks..."

    # Check if pre-commit is installed
    if ! command_exists pre-commit; then
        print_info "Installing pre-commit..."
        pip install pre-commit
    fi

    pre-commit install
    print_success "Pre-commit hooks configured"
else
    print_warning ".pre-commit-config.yaml not found - skipping hooks"
fi

# ============================================================================
# Create Environment Files
# ============================================================================

print_header "Step 10: Creating Environment Files"

# Backend .env
if [ ! -f ".env" ]; then
    print_info "Creating backend .env file..."
    cat > .env << 'EOF'
# PokerTool Backend Configuration
# Copy this file to .env and customize as needed

# Database Configuration
POKER_DB_TYPE=sqlite
POKER_DB_PATH=poker_decisions.db

# For PostgreSQL (optional):
# POKER_DB_TYPE=postgresql
# POKER_DB_HOST=localhost
# POKER_DB_PORT=5432
# POKER_DB_NAME=pokertool
# POKER_DB_USER=pokertool_user
# POKER_DB_PASSWORD=your_password_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=5001

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
EOF
    print_success "Created .env file"
else
    print_info ".env file already exists"
fi

# Frontend .env
if [ -d "pokertool-frontend" ] && [ ! -f "pokertool-frontend/.env" ]; then
    print_info "Creating frontend .env file..."
    cat > pokertool-frontend/.env << 'EOF'
# PokerTool Frontend Configuration
# Copy from .env.example and customize as needed

REACT_APP_API_URL=http://localhost:5001
REACT_APP_WS_URL=http://localhost:8000
EOF
    print_success "Created frontend .env file"
else
    print_info "Frontend .env file already exists or frontend not found"
fi

# ============================================================================
# Run Initial Tests
# ============================================================================

print_header "Step 11: Running Initial Tests"

print_info "Running quick validation..."

# Test Python import
python -c "import pokertool; print('✓ Python package imports successfully')" 2>/dev/null && \
    print_success "Python package validated" || \
    print_warning "Python package validation failed (may be expected if not installed in develop mode)"

# Check database
if [ -f "src/pokertool/database.py" ]; then
    print_info "Database module found"
fi

# ============================================================================
# Summary and Next Steps
# ============================================================================

print_header "Setup Complete!"

echo -e "${GREEN}✓ Development environment is ready!${NC}\n"

echo "Next steps:"
echo ""
echo "1. Activate the virtual environment (in new terminals):"
echo "   ${BLUE}source .venv/bin/activate${NC}"
echo ""
echo "2. Start the backend API server:"
echo "   ${BLUE}PYTHONPATH=src .venv/bin/python -m uvicorn pokertool.api:create_app --host 0.0.0.0 --port 5001 --factory${NC}"
echo ""

if command_exists node && [ -d "pokertool-frontend" ]; then
    echo "3. Start the frontend development server (in another terminal):"
    echo "   ${BLUE}cd pokertool-frontend && npm start${NC}"
    echo ""
fi

echo "4. Run tests:"
echo "   ${BLUE}.venv/bin/pytest tests/ -v${NC}"
echo ""
echo "5. View documentation:"
echo "   ${BLUE}docs/CONFIGURATION.md${NC} - Environment configuration"
echo "   ${BLUE}CONTRIBUTING.md${NC} - Development guidelines"
echo ""

print_info "For more information, see README.md"

# Deactivate virtual environment
deactivate 2>/dev/null || true

print_success "Setup script completed successfully!"
