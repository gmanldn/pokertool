#!/bin/bash
# first_run_mac.sh - Complete bootstrap script for macOS
# This script ensures Python 3.8+ is installed and sets up PokerTool from scratch

set -e  # Exit on error

echo "=================================="
echo "PokerTool - macOS Bootstrap"
echo "=================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check macOS version
log_info "Checking macOS version..."
if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "This script is for macOS only"
    exit 1
fi

MACOS_VERSION=$(sw_vers -productVersion)
log_info "macOS version: $MACOS_VERSION"

# Check for Xcode Command Line Tools (required for Homebrew)
log_info "Checking for Xcode Command Line Tools..."
if ! xcode-select -p &> /dev/null; then
    log_warn "Xcode Command Line Tools not found. Installing..."
    xcode-select --install
    log_info "Please complete the Xcode Command Line Tools installation in the dialog"
    log_info "Then re-run this script"
    exit 0
else
    log_info "✓ Xcode Command Line Tools installed"
fi

# Check for Homebrew
log_info "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    log_warn "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    log_info "✓ Homebrew installed"
else
    log_info "✓ Homebrew already installed"
fi

# Check for Python 3
log_info "Checking for Python 3..."
PYTHON_CMD=""

# Try to find Python 3
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Found Python: $PYTHON_VERSION"
    
    # Check if version is 3.8 or higher
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        log_warn "Python $PYTHON_VERSION is too old (need 3.8+)"
        PYTHON_CMD=""
    fi
fi

# Install Python if not found or too old
if [ -z "$PYTHON_CMD" ]; then
    log_warn "Python 3.8+ not found. Installing Python via Homebrew..."
    brew install python@3.11
    
    # Refresh PATH
    export PATH="/usr/local/opt/python@3.11/bin:$PATH"
    export PATH="/opt/homebrew/opt/python@3.11/bin:$PATH"
    
    PYTHON_CMD="python3"
    log_info "✓ Python installed"
else
    log_info "✓ Python 3.8+ already installed"
fi

# Verify Python is accessible
if ! command -v $PYTHON_CMD &> /dev/null; then
    log_error "Python installation failed or not in PATH"
    log_error "Please install Python 3.8+ manually from https://www.python.org"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
log_info "Using: $PYTHON_VERSION"

# Check for pip
log_info "Checking for pip..."
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    log_warn "pip not found. Installing pip..."
    $PYTHON_CMD -m ensurepip --upgrade
    log_info "✓ pip installed"
else
    log_info "✓ pip already installed"
fi

# Optional: Install Tesseract (for OCR functionality)
log_info "Checking for Tesseract OCR..."
if ! command -v tesseract &> /dev/null; then
    log_warn "Tesseract not found. Installing (required for screen scraping)..."
    brew install tesseract
    log_info "✓ Tesseract installed"
else
    log_info "✓ Tesseract already installed"
fi

# Optional: Check for Node.js (for frontend development)
log_info "Checking for Node.js..."
if ! command -v node &> /dev/null; then
    log_warn "Node.js not found. Installing (optional, for frontend features)..."
    brew install node
    log_info "✓ Node.js installed"
else
    log_info "✓ Node.js already installed: $(node --version)"
fi

# Make start.py executable
if [ -f "start.py" ]; then
    chmod +x start.py
    log_info "✓ Made start.py executable"
fi

echo ""
echo "=================================="
log_info "Bootstrap complete! Launching PokerTool..."
echo "=================================="
echo ""

# Run start.py
$PYTHON_CMD start.py "$@"

exit $?
