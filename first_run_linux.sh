#!/bin/bash
# first_run_linux.sh - Complete bootstrap script for Linux
# This script ensures Python 3.8+ is installed and sets up PokerTool from scratch

set -e  # Exit on error

echo "=================================="
echo "PokerTool - Linux Bootstrap"
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

# Detect Linux distribution
log_info "Detecting Linux distribution..."

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
    log_info "Detected: $PRETTY_NAME"
else
    log_error "Cannot detect Linux distribution"
    exit 1
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
    log_warn "Python 3.8+ not found. Installing Python..."
    
    case $OS in
        ubuntu|debian)
            log_info "Installing Python on Ubuntu/Debian..."
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip python3-venv python3-dev
            ;;
        fedora|rhel|centos)
            log_info "Installing Python on Fedora/RHEL/CentOS..."
            sudo dnf install -y python3 python3-pip python3-devel
            ;;
        arch|manjaro)
            log_info "Installing Python on Arch/Manjaro..."
            sudo pacman -S --noconfirm python python-pip
            ;;
        opensuse*)
            log_info "Installing Python on openSUSE..."
            sudo zypper install -y python3 python3-pip python3-devel
            ;;
        *)
            log_error "Unsupported distribution: $OS"
            log_error "Please install Python 3.8+ manually"
            exit 1
            ;;
    esac
    
    PYTHON_CMD="python3"
    log_info "✓ Python installed"
else
    log_info "✓ Python 3.8+ already installed"
fi

# Verify Python is accessible
if ! command -v $PYTHON_CMD &> /dev/null; then
    log_error "Python installation failed or not in PATH"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version)
log_info "Using: $PYTHON_VERSION"

# Check for pip
log_info "Checking for pip..."
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    log_warn "pip not found. Installing pip..."
    
    case $OS in
        ubuntu|debian)
            sudo apt-get install -y python3-pip
            ;;
        fedora|rhel|centos)
            sudo dnf install -y python3-pip
            ;;
        *)
            $PYTHON_CMD -m ensurepip --upgrade
            ;;
    esac
    
    log_info "✓ pip installed"
else
    log_info "✓ pip already installed"
fi

# Install system dependencies
log_info "Installing system dependencies..."

case $OS in
    ubuntu|debian)
        log_info "Installing dependencies on Ubuntu/Debian..."
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            libssl-dev \
            libffi-dev \
            python3-dev \
            tesseract-ocr \
            libopencv-dev \
            python3-opencv
        ;;
    fedora|rhel|centos)
        log_info "Installing dependencies on Fedora/RHEL/CentOS..."
        sudo dnf install -y \
            gcc \
            gcc-c++ \
            make \
            openssl-devel \
            libffi-devel \
            python3-devel \
            tesseract \
            opencv-devel
        ;;
    arch|manjaro)
        log_info "Installing dependencies on Arch/Manjaro..."
        sudo pacman -S --noconfirm \
            base-devel \
            openssl \
            libffi \
            tesseract \
            opencv \
            python-opencv
        ;;
    opensuse*)
        log_info "Installing dependencies on openSUSE..."
        sudo zypper install -y \
            gcc \
            gcc-c++ \
            make \
            libopenssl-devel \
            libffi-devel \
            python3-devel \
            tesseract-ocr \
            opencv-devel
        ;;
esac

log_info "✓ System dependencies installed"

# Optional: Install Node.js
log_info "Checking for Node.js..."
if ! command -v node &> /dev/null; then
    log_warn "Node.js not found. Installing (optional, for frontend features)..."
    
    case $OS in
        ubuntu|debian)
            # Install Node.js via NodeSource
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
        fedora|rhel|centos)
            curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
            sudo dnf install -y nodejs
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm nodejs npm
            ;;
        opensuse*)
            sudo zypper install -y nodejs npm
            ;;
    esac
    
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
