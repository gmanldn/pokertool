#!/bin/bash
# first_run_linux.sh - Super Reliable Linux Bootstrap Script  
# Supports Ubuntu, Debian, Fedora, RHEL, CentOS, Arch, Manjaro, openSUSE

set -u
set -o pipefail

echo "=================================="
echo "PokerTool - Linux Bootstrap"
echo "=================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT" || { echo "ERROR: Cannot navigate to project root"; exit 1; }

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

INSTALL_ERRORS=0
INSTALL_WARNINGS=0

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((INSTALL_WARNINGS++)); }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; ((INSTALL_ERRORS++)); }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

retry_command() {
    local max_attempts=3 attempt=1 delay=2
    while [ $attempt -le $max_attempts ]; do
        if eval "$@"; then return 0; fi
        if [ $attempt -lt $max_attempts ]; then
            log_warn "Command failed (attempt $attempt/$max_attempts). Retrying in ${delay}s..."
            sleep $delay; delay=$((delay * 2))
        fi
        attempt=$((attempt + 1))
    done
    return 1
}

log_step "Detecting Linux distribution..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID; VER=${VERSION_ID:-unknown}
    log_info "Detected: ${PRETTY_NAME:-$OS $VER}"
else
    log_error "Cannot detect Linux distribution"
    exit 1
fi

log_step "Checking for Python 3.8+..."
PYTHON_CMD=""
for cmd in python3 python3.11 python3.10 python3.9 python3.8 python; do
    if command -v "$cmd" &> /dev/null; then
        version=$($cmd --version 2>&1 | awk '{print $2}' | head -n1)
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
            PYTHON_CMD=$cmd
            log_info "✓ Found Python $version"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    log_warn "Python 3.8+ not found. Installing..."
    case $OS in
        ubuntu|debian|linuxmint)
            retry_command 'sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv python3-dev build-essential' || \
                { log_error "Failed to install Python"; exit 1; }
            ;;
        fedora|rhel|centos|rocky|almalinux)
            retry_command 'sudo dnf install -y python3 python3-pip python3-devel gcc gcc-c++ make' || \
                { log_error "Failed to install Python"; exit 1; }
            ;;
        arch|manjaro)
            retry_command 'sudo pacman -S --noconfirm python python-pip base-devel' || \
                { log_error "Failed to install Python"; exit 1; }
            ;;
        opensuse*|sles)
            retry_command 'sudo zypper install -y python3 python3-pip python3-devel gcc gcc-c++ make' || \
                { log_error "Failed to install Python"; exit 1; }
            ;;
        *)
            log_error "Unsupported distribution: $OS"
            exit 1
            ;;
    esac
    PYTHON_CMD=python3
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
log_info "Using: $PYTHON_VERSION"

log_step "Installing system dependencies..."
case $OS in
    ubuntu|debian|linuxmint)
        retry_command 'sudo apt-get install -y tesseract-ocr libopencv-dev python3-opencv libssl-dev libffi-dev' || \
            log_warn "Some dependencies failed to install"
        ;;
    fedora|rhel|centos|rocky|almalinux)
        retry_command 'sudo dnf install -y tesseract opencv-devel openssl-devel libffi-devel' || \
            log_warn "Some dependencies failed to install"
        ;;
    arch|manjaro)
        retry_command 'sudo pacman -S --noconfirm tesseract opencv python-opencv openssl libffi' || \
            log_warn "Some dependencies failed to install"
        ;;
    opensuse*|sles)
        retry_command 'sudo zypper install -y tesseract-ocr opencv-devel libopenssl-devel libffi-devel' || \
            log_warn "Some dependencies failed to install"
        ;;
esac
log_info "✓ System dependencies installed"

log_step "Checking for Node.js (optional)..."
if ! command -v node &> /dev/null; then
    log_warn "Node.js not found. Installing..."
    case $OS in
        ubuntu|debian|linuxmint)
            if retry_command 'curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - && sudo apt-get install -y nodejs'; then
                log_info "✓ Node.js installed"
            else
                log_warn "Node.js installation failed (optional)"
            fi
            ;;
        fedora|rhel|centos|rocky|almalinux)
            if retry_command 'curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash - && sudo dnf install -y nodejs'; then
                log_info "✓ Node.js installed"
            else
                log_warn "Node.js installation failed (optional)"
            fi
            ;;
        arch|manjaro)
            retry_command 'sudo pacman -S --noconfirm nodejs npm' || log_warn "Node.js installation failed (optional)"
            ;;
        opensuse*|sles)
            retry_command 'sudo zypper install -y nodejs npm' || log_warn "Node.js installation failed (optional)"
            ;;
    esac
else
    log_info "✓ Node.js already installed: $(node --version 2>&1)"
fi

[ -f "start.py" ] && chmod +x start.py 2>/dev/null

echo ""
log_step "Bootstrap Summary"
echo "====================================="
[ $INSTALL_ERRORS -eq 0 ] && log_info "✓ Bootstrap completed successfully!" || log_error "Completed with $INSTALL_ERRORS error(s)"
[ $INSTALL_WARNINGS -gt 0 ] && log_warn "Completed with $INSTALL_WARNINGS warning(s)"
echo ""
log_step "Launching PokerTool setup..."
echo "====================================="
echo ""

$PYTHON_CMD start.py "$@"
exit $?
