# First Run Guide - Complete Bootstrap Instructions

This guide helps you set up PokerTool from absolutely nothing, including installing Python if needed.

---

## Quick Start (Choose Your OS)

### 🍎 macOS
```bash
# Run from project root
./scripts/first_run_mac.sh

# Or from scripts directory
cd scripts && ./first_run_mac.sh
```

### 🐧 Linux
```bash
# Run from project root
./scripts/first_run_linux.sh

# Or from scripts directory
cd scripts && ./first_run_linux.sh
```

### 🪟 Windows
```powershell
# Run from project root
.\scripts\first_run_windows.ps1

# Or from scripts directory
cd scripts
.\first_run_windows.ps1
```

---

## What These Scripts Do

The first-run scripts are located in the `scripts/` directory and automatically navigate to the project root before executing. They perform a complete bootstrap:

1. ✅ **Check for Python 3.8+**
   - If not found, automatically installs Python
   - Verifies version compatibility

2. ✅ **Install Package Managers** (if needed)
   - macOS: Homebrew
   - Windows: Uses winget or direct installer
   - Linux: Uses native package manager (apt, dnf, pacman, etc.)

3. ✅ **Install System Dependencies**
   - Build tools (gcc, make, etc.)
   - Tesseract OCR (for screen scraping)
   - OpenCV libraries
   - Development headers

4. ✅ **Install Node.js** (optional)
   - For frontend features
   - Can skip if not needed

5. ✅ **Run PokerTool Setup**
   - Creates virtual environment
   - Installs Python dependencies
   - Configures the application
   - Launches PokerTool

---

## Platform-Specific Details

### macOS Requirements

**Minimum:** macOS 10.13 (High Sierra) or later  
**Recommended:** macOS 12.0 (Monterey) or later

**What will be installed:**

- Xcode Command Line Tools (if not present)
- Homebrew (if not present)
- Python 3.11 via Homebrew
- Tesseract OCR
- Node.js (optional)

**Manual Installation (if script fails):**
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install dependencies
brew install tesseract node

# Navigate to project root and run PokerTool
cd /path/to/pokertool
python3 start.py
```

---

### Linux Requirements

**Supported Distributions:**

- Ubuntu 20.04+ / Debian 10+
- Fedora 35+ / RHEL 8+ / CentOS 8+
- Arch Linux / Manjaro
- openSUSE Leap 15.3+

**What will be installed:**

- Python 3.8+ and pip
- Build essentials (gcc, make, etc.)
- Python development headers
- Tesseract OCR
- OpenCV libraries
- Node.js (optional)

**Manual Installation Examples:**

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv \
    build-essential python3-dev tesseract-ocr \
    libopencv-dev python3-opencv

cd /path/to/pokertool
python3 start.py
```

**Fedora/RHEL:**
```bash
sudo dnf install -y python3 python3-pip python3-devel \
    gcc gcc-c++ make tesseract opencv-devel

cd /path/to/pokertool
python3 start.py
```

**Arch/Manjaro:**
```bash
sudo pacman -S python python-pip base-devel \
    tesseract opencv python-opencv

cd /path/to/pokertool
python3 start.py
```

---

### Windows Requirements

**Minimum:** Windows 10 (1809) or later  
**Recommended:** Windows 11

**What will be installed:**

- Python 3.11 (via winget or direct installer)
- pip (Python package manager)

**Optional (recommended for full functionality):**

- Visual C++ Build Tools
- Tesseract OCR
- Node.js

**Manual Installation (if script fails):**

1. **Install Python:**
   - Download from: https://www.python.org/downloads/
   - **Important:** Check "Add Python to PATH" during installation

2. **Install Visual C++ Build Tools:**
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Install "Desktop development with C++" workload

3. **Install Tesseract OCR:**
   - Download from: https://github.com/UB-Mannheim/tesseract/wiki
   - Or use: `winget install UB-Mannheim.TesseractOCR`

4. **Run PokerTool:**

   ```powershell
   ```powershell
   python start.py
   ```

---

## Troubleshooting

### Python Not Found After Installation

**macOS/Linux:**
```bash
# Check if Python is installed
which python3
python3 --version

# If not in PATH, try absolute path
/usr/local/bin/python3 start.py
```

**Windows:**
```powershell
# Check if Python is installed
where python
python --version

# Refresh environment
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Or restart terminal/computer
```

---

### Permission Denied (macOS/Linux)

```bash
# Make script executable
chmod +x first_run_mac.sh   # or first_run_linux.sh

# Then run
./first_run_mac.sh
```

---

### Execution Policy Error (Windows)

```powershell
# Run as Administrator, then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run the script
.\first_run_windows.ps1
```

---

### Missing Dependencies

If the automated installation fails, you can install dependencies manually:

**macOS:**
```bash
brew install python@3.11 tesseract opencv node
python3 start.py
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3 python3-pip tesseract-ocr python3-opencv
python3 start.py
```

**Windows:**

- Install Python from: https://www.python.org
- Install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Run: `python start.py`

---

### Build Errors (Missing Compilers)

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# Fedora/RHEL
sudo dnf groupinstall "Development Tools"
sudo dnf install python3-devel

# Arch
sudo pacman -S base-devel
```

**Windows:**

- Install Visual C++ Build Tools from:

  https://visualstudio.microsoft.com/visual-cpp-build-tools/
  https://visualstudio.microsoft.com/visual-cpp-build-tools/

---

## After Installation

Once the first-run script completes, you can use PokerTool normally:

```bash
# macOS/Linux
python3 start.py

# Windows
python start.py
```

### Available Commands

```bash
# Full setup and launch (default)
python3 start.py

# Launch only (after setup)
python3 start.py --launch

# Validate installation
python3 start.py --validate

# Run in test mode
python3 start.py --launch
# Then: pokertool test

# Run comprehensive self-test
python3 start.py --self-test

# Setup virtual environment only
python3 start.py --venv

# Install Python dependencies only
python3 start.py --python

# Install Node.js dependencies only
python3 start.py --node

# Run tests
python3 start.py --tests
```

---

## Verifying Installation

After the first run completes, verify everything works:

```bash
# Check Python version
python3 --version  # Should be 3.8 or higher

# Check virtual environment
ls .venv  # Should exist

# Run validation
python3 start.py --validate

# Should output:
# ✓ Python standard library
# ✓ NumPy
# ✓ OpenCV
# ✓ Pillow
# ✓ Setup validation complete
```

---

## Common Issues & Solutions

### Issue: "Command not found: python3"
**Solution:** Python is not in your PATH. Try:

- macOS/Linux: Use absolute path `/usr/local/bin/python3`
- Windows: Reinstall Python and check "Add to PATH"
- Or restart your terminal/computer

---

### Issue: "Permission denied" when running scripts
**Solution:**
```bash
chmod +x first_run_mac.sh
./first_run_mac.sh
```

---

### Issue: "pip is not recognized"
**Solution:**
```bash
# macOS/Linux
python3 -m ensurepip --upgrade

# Windows
python -m ensurepip --upgrade
```

---

### Issue: Virtual environment creation fails
**Solution:**
```bash
# Install venv module
# Ubuntu/Debian:
sudo apt-get install python3-venv

# Then try again
python3 start.py
```

---

### Issue: OpenCV or NumPy installation fails
**Solution:**
This usually means missing build tools.

**macOS:**
```bash
xcode-select --install
```

**Linux:**
```bash
sudo apt-get install build-essential python3-dev  # Ubuntu/Debian
sudo dnf groupinstall "Development Tools"          # Fedora/RHEL
```

**Windows:**

- Install Visual C++ Build Tools
- Or use pre-built wheels: `pip install opencv-python-headless`

---

### Issue: Screen capture/OCR not working
**Solution:**
Install Tesseract OCR:

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr  # Ubuntu/Debian
sudo dnf install tesseract           # Fedora/RHEL
```

**Windows:**
```powershell
winget install UB-Mannheim.TesseractOCR
```

---

## Network/Proxy Issues

If you're behind a corporate firewall or proxy:

**Set proxy for pip:**
```bash
# macOS/Linux
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# Windows (PowerShell)
$env:HTTP_PROXY="http://proxy.company.com:8080"
$env:HTTPS_PROXY="http://proxy.company.com:8080"

# Then run
python3 start.py
```

**Set proxy for npm (if using Node.js features):**
```bash
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080
```

---

## Offline Installation

If you need to install without internet access:

1. **Download dependencies on a machine with internet:**

   ```bash
   ```bash
   pip download -r requirements.txt -d packages/
   ```

2. **Transfer the `packages/` folder to the offline machine**

3. **Install from local packages:**

   ```bash
   ```bash
   pip install --no-index --find-links=packages/ -r requirements.txt
   ```

---

## Getting Help

If you encounter issues not covered here:

1. **Check the logs:**

   ```bash
   ```bash
   cat logs/master_log.txt  # macOS/Linux
   type logs\master_log.txt  # Windows
   ```

2. **Run with verbose output:**

   ```bash
   ```bash
   python3 start.py --validate
   ```

3. **Check Python version:**

   ```bash
   ```bash
   python3 --version
   # Must be 3.8 or higher
   ```

4. **Verify dependencies:**

   ```bash
   ```bash
   python3 -c "import numpy, cv2, PIL; print('Dependencies OK')"
   ```

---

## Next Steps

After successful installation:

1. **Read the main README.md** for usage instructions
2. **Run the test mode** to verify all features work
3. **Configure your settings** in `poker_config.json`
4. **Start using PokerTool!**

---

## Quick Reference

| OS | Command | Python Command |
|---|---|---|
| macOS | `./first_run_mac.sh` | `python3` |
| Linux | `./first_run_linux.sh` | `python3` |
| Windows | `.\first_run_windows.ps1` | `python` or `py` |

---

## Minimum System Requirements

- **OS:** macOS 10.13+ / Windows 10+ / Ubuntu 20.04+ (or equivalent)
- **RAM:** 4 GB (8 GB recommended)
- **Disk:** 2 GB free space
- **Python:** 3.8 or higher
- **Internet:** Required for initial setup

---

**Last Updated:** October 21, 2025
**PokerTool Version:** 99.0.0
