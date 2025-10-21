#!/bin/bash
# first_run_mac.sh - Super Reliable macOS Bootstrap Script
# This script ensures Python 3.8+ is installed and sets up PokerTool from scratch
# with comprehensive error handling and recovery mechanisms

# DO NOT use set -e - we want to handle errors gracefully
set -u  # Exit on undefined variables
set -o pipefail  # Catch errors in pipelines

echo "=================================="
echo "PokerTool - macOS Bootstrap"
echo "=================================="
echo ""

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT" || {
    echo "ERROR: Cannot navigate to project root"
    exit 1
}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Track installation status
INSTALL_ERRORS=0
INSTALL_WARNINGS=0

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((INSTALL_WARNINGS++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((INSTALL_ERRORS++))
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Retry function for network operations
retry_command() {
    local max_attempts=3
    local attempt=1
    local delay=2
    local command="$@"

    while [ $attempt -le $max_attempts ]; do
        if eval "$command"; then
            return 0
        fi

        if [ $attempt -lt $max_attempts ]; then
            log_warn "Command failed (attempt $attempt/$max_attempts). Retrying in ${delay}s..."
            sleep $delay
            delay=$((delay * 2))
        fi
        attempt=$((attempt + 1))
    done

    return 1
}

# Validate command exists and is executable
validate_command() {
    local cmd=$1
    local name=${2:-$1}

    if command -v "$cmd" &> /dev/null; then
        log_info "✓ $name is available"
        return 0
    else
        log_error "✗ $name not found or not executable"
        return 1
    fi
}

# ====================
# STEP 1: System Checks
# ====================
log_step "Verifying macOS system..."

if [[ "$OSTYPE" != "darwin"* ]]; then
    log_error "This script is for macOS only. Detected: $OSTYPE"
    exit 1
fi

MACOS_VERSION=$(sw_vers -productVersion 2>/dev/null || echo "unknown")
log_info "macOS version: $MACOS_VERSION"

# Detect architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "arm64" ]]; then
    log_info "Detected Apple Silicon (ARM64)"
    HOMEBREW_PREFIX="/opt/homebrew"
else
    log_info "Detected Intel (x86_64)"
    HOMEBREW_PREFIX="/usr/local"
fi

# =================================
# STEP 2: Xcode Command Line Tools
# =================================
log_step "Checking Xcode Command Line Tools..."

if ! xcode-select -p &> /dev/null; then
    log_warn "Xcode Command Line Tools not found."

    # Check if installation is already in progress
    if pgrep -q "Install Command Line"; then
        log_info "Installation appears to be in progress. Waiting..."
        log_info "Please complete the installation and re-run this script."
        exit 0
    fi

    log_info "Triggering installation..."
    if xcode-select --install 2>&1 | grep -q "already installed"; then
        log_info "✓ Xcode Command Line Tools already installed (but not detected)"
        # Force selection of installed tools
        sudo xcode-select --reset 2>/dev/null || true
    else
        log_info "Please complete the Xcode Command Line Tools installation dialog."
        log_info "After installation completes, re-run this script:"
        echo ""
        echo "  cd $PROJECT_ROOT"
        echo "  ./scripts/first_run_mac.sh"
        echo ""
        exit 0
    fi
else
    XCODE_PATH=$(xcode-select -p)
    log_info "✓ Xcode Command Line Tools installed at: $XCODE_PATH"
fi

# ====================
# STEP 3: Homebrew
# ====================
log_step "Checking for Homebrew..."

if ! command -v brew &> /dev/null; then
    log_warn "Homebrew not found. Installing..."

    log_info "Downloading and running Homebrew installer..."
    if retry_command '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'; then
        log_info "✓ Homebrew installation completed"

        # Set up Homebrew environment
        if [[ -f "$HOMEBREW_PREFIX/bin/brew" ]]; then
            eval "$($HOMEBREW_PREFIX/bin/brew shellenv)"

            # Add to shell profile
            for profile in ~/.zprofile ~/.bash_profile ~/.profile; do
                if [[ -f "$profile" ]] || [[ "$profile" == ~/.zprofile ]]; then
                    if ! grep -q "brew shellenv" "$profile" 2>/dev/null; then
                        echo "" >> "$profile"
                        echo '# Homebrew' >> "$profile"
                        echo "eval \"\$($HOMEBREW_PREFIX/bin/brew shellenv)\"" >> "$profile"
                        log_info "Added Homebrew to $profile"
                    fi
                    break
                fi
            done
        else
            log_error "Homebrew binary not found at expected location: $HOMEBREW_PREFIX/bin/brew"
            log_error "You may need to install Homebrew manually: https://brew.sh"
        fi
    else
        log_error "Homebrew installation failed after multiple attempts"
        log_error "Please install manually from https://brew.sh and re-run this script"
        exit 1
    fi
else
    log_info "✓ Homebrew already installed"
    BREW_VERSION=$(brew --version | head -n1)
    log_info "  Version: $BREW_VERSION"

    # Update Homebrew
    log_info "Updating Homebrew..."
    if retry_command 'brew update'; then
        log_info "✓ Homebrew updated"
    else
        log_warn "Failed to update Homebrew (continuing anyway)"
    fi
fi

# Validate Homebrew is working
if ! validate_command brew "Homebrew"; then
    log_error "Homebrew installation appears incomplete"
    exit 1
fi

# ==================
# STEP 4: Python 3
# ==================
log_step "Checking for Python 3.8+..."

PYTHON_CMD=""
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=8

# Function to check Python version
check_python_version() {
    local python_cmd=$1

    if ! command -v "$python_cmd" &> /dev/null; then
        return 1
    fi

    local version=$($python_cmd --version 2>&1 | awk '{print $2}' | head -n1)
    local major=$(echo "$version" | cut -d. -f1)
    local minor=$(echo "$version" | cut -d. -f2)

    if [ "$major" -lt $MIN_PYTHON_MAJOR ] || \
       ([ "$major" -eq $MIN_PYTHON_MAJOR ] && [ "$minor" -lt $MIN_PYTHON_MINOR ]); then
        log_info "Found Python $version (too old, need ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+)"
        return 1
    fi

    log_info "Found Python $version ✓"
    echo "$python_cmd"
    return 0
}

# Try multiple Python commands
for cmd in python3 python3.11 python3.10 python3.9 python3.8 python; do
    if PYTHON_CMD=$(check_python_version "$cmd"); then
        break
    fi
done

# Install Python if not found
if [ -z "$PYTHON_CMD" ]; then
    log_warn "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ not found. Installing via Homebrew..."

    if retry_command 'brew install python@3.11'; then
        log_info "✓ Python 3.11 installed"

        # Add to PATH
        export PATH="$HOMEBREW_PREFIX/opt/python@3.11/bin:$PATH"

        # Try to find it again
        for cmd in python3.11 python3; do
            if PYTHON_CMD=$(check_python_version "$cmd"); then
                break
            fi
        done

        if [ -z "$PYTHON_CMD" ]; then
            log_error "Python installed but cannot be found. Check PATH configuration."
            log_error "Try running: export PATH=\"$HOMEBREW_PREFIX/opt/python@3.11/bin:\$PATH\""
            exit 1
        fi
    else
        log_error "Failed to install Python via Homebrew"
        log_error "Please install Python 3.8+ manually from https://www.python.org"
        exit 1
    fi
else
    log_info "✓ Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ already installed"
fi

# Validate Python is accessible
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
log_info "Using: $PYTHON_VERSION (command: $PYTHON_CMD)"

# =============
# STEP 5: pip
# =============
log_step "Checking for pip..."

if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    log_warn "pip not found. Installing..."

    if $PYTHON_CMD -m ensurepip --upgrade; then
        log_info "✓ pip installed"
    else
        log_error "Failed to install pip"
        log_error "Try running: $PYTHON_CMD -m ensurepip --upgrade"
        exit 1
    fi
else
    PIP_VERSION=$($PYTHON_CMD -m pip --version)
    log_info "✓ pip available: $PIP_VERSION"
fi

# Upgrade pip to latest version
log_info "Upgrading pip to latest version..."
if $PYTHON_CMD -m pip install --upgrade pip setuptools wheel 2>/dev/null; then
    log_info "✓ pip upgraded"
else
    log_warn "Could not upgrade pip (continuing anyway)"
fi

# ====================
# STEP 6: Tesseract
# ====================
log_step "Checking for Tesseract OCR (required for screen scraping)..."

if ! command -v tesseract &> /dev/null; then
    log_warn "Tesseract not found. Installing..."

    if retry_command 'brew install tesseract'; then
        log_info "✓ Tesseract installed"
        validate_command tesseract "Tesseract OCR"
    else
        log_warn "Failed to install Tesseract"
        log_warn "Screen scraping features may not work"
        log_warn "You can install later with: brew install tesseract"
    fi
else
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n1)
    log_info "✓ Tesseract already installed: $TESSERACT_VERSION"
fi

# ==================
# STEP 7: Node.js
# ==================
log_step "Checking for Node.js (optional, for frontend features)..."

if ! command -v node &> /dev/null; then
    log_warn "Node.js not found. Installing..."

    if retry_command 'brew install node'; then
        log_info "✓ Node.js installed"
        validate_command node "Node.js"
        validate_command npm "npm"
    else
        log_warn "Failed to install Node.js"
        log_warn "Frontend features may be limited"
        log_warn "You can install later with: brew install node"
    fi
else
    NODE_VERSION=$(node --version 2>&1)
    NPM_VERSION=$(npm --version 2>&1)
    log_info "✓ Node.js already installed: $NODE_VERSION"
    log_info "✓ npm version: $NPM_VERSION"
fi

# ===========================
# STEP 8: Prepare start.py
# ===========================
log_step "Preparing PokerTool launcher..."

if [ -f "start.py" ]; then
    chmod +x start.py 2>/dev/null || true
    log_info "✓ Made start.py executable"
else
    log_error "start.py not found in $PROJECT_ROOT"
    log_error "Are you in the correct directory?"
    exit 1
fi

# ====================
# STEP 9: Summary
# ====================
echo ""
echo "====================================="
log_step "Bootstrap Summary"
echo "====================================="

if [ $INSTALL_ERRORS -eq 0 ]; then
    log_info "✓ Bootstrap completed successfully!"
    if [ $INSTALL_WARNINGS -gt 0 ]; then
        log_warn "Completed with $INSTALL_WARNINGS warning(s)"
    fi
else
    log_error "Bootstrap completed with $INSTALL_ERRORS error(s) and $INSTALL_WARNINGS warning(s)"
    log_error "Some features may not work correctly"
fi

echo ""
echo "Installed components:"
echo "  - Python: $PYTHON_VERSION"
echo "  - Homebrew: $(brew --version | head -n1)"
[ command -v tesseract &> /dev/null ] && echo "  - Tesseract: $(tesseract --version 2>&1 | head -n1)"
[ command -v node &> /dev/null ] && echo "  - Node.js: $(node --version)"
echo ""

# ==========================
# STEP 10: Launch PokerTool
# ==========================
log_step "Launching PokerTool setup..."
echo "====================================="
echo ""

# Execute start.py with all arguments passed to this script
if $PYTHON_CMD start.py "$@"; then
    echo ""
    log_info "PokerTool setup completed successfully!"
    exit 0
else
    EXIT_CODE=$?
    echo ""
    log_error "PokerTool setup encountered an error (exit code: $EXIT_CODE)"
    log_error "Check the output above for details"
    exit $EXIT_CODE
fi
