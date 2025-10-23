# Installation Requirements Matrix

## Minimum Requirements

### All Platforms

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Python** | 3.9 | 3.12 | Python 3.13 supported but not extensively tested |
| **RAM** | 2GB | 4GB+ | More for better ML performance |
| **Disk Space** | 500MB | 2GB+ | Includes dependencies and data |
| **CPU** | 2 cores | 4+ cores | More cores improve scraping performance |

### Operating Systems

#### macOS
| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **OS Version** | macOS 12 (Monterey) | macOS 14+ (Sonoma) | Tested on 12, 13, 14 |
| **Xcode Tools** | Required | Latest | `xcode-select --install` |
| **Homebrew** | Optional | Recommended | For easy dependency installation |

**Installation Command:**
```bash
brew install git node python@3.12
```

#### Linux (Ubuntu/Debian)
| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **OS Version** | Ubuntu 20.04 | Ubuntu 24.04 | Also tested on Debian 11+ |
| **Build Tools** | Required | Latest | `build-essential` package |

**Installation Command:**
```bash
sudo apt-get update
sudo apt-get install -y git nodejs npm python3 python3-pip python3-venv build-essential
```

#### Linux (RHEL/CentOS)
| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **OS Version** | RHEL 8 | RHEL 9 | Also works on Rocky/Alma Linux |
| **Development Tools** | Required | Latest | Development Tools group |

**Installation Command:**
```bash
sudo yum groupinstall "Development Tools"
sudo yum install git nodejs npm python3 python3-pip
```

#### Windows
| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **OS Version** | Windows 10 | Windows 11 | 64-bit required |
| **Visual C++** | 2015+ | Latest | For compiling native modules |
| **PowerShell** | 5.1 | 7.0+ | For installation scripts |

**Installation Steps:**
1. Download and install [Python 3.12](https://www.python.org/downloads/)
2. Download and install [Node.js LTS](https://nodejs.org/)
3. Download and install [Git for Windows](https://git-scm.com/download/win)

## Network Requirements

### Required Connectivity

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| **PyPI** | 443 | HTTPS | Python package downloads |
| **npm Registry** | 443 | HTTPS | Node.js package downloads |
| **GitHub** | 443 | HTTPS | Repository access |

### Optional Connectivity

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| **Poker Site** | 443 | HTTPS | Live poker table scraping |
| **Chrome DevTools** | 9222 | WS | Remote debugging for scraping |

## System Dependencies

### Python Packages

Core dependencies (automatically installed):
- numpy >= 2.0.0
- Pillow >= 10.0.0
- opencv-python-headless >= 4.8.0
- pytesseract >= 0.3.10
- mss >= 9.0.0
- fastapi >= 0.100.0
- uvicorn >= 0.23.0

### System Packages

#### macOS
```bash
brew install tesseract  # OCR engine (optional but recommended)
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get install tesseract-ocr libtesseract-dev
```

#### Windows
Download Tesseract OCR from: https://github.com/UB-Mannheim/tesseract/wiki

## Performance Considerations

### For Basic Use (1-2 tables)
- 2 CPU cores
- 2GB RAM
- 500MB disk space

### For Standard Use (3-4 tables)
- 4 CPU cores
- 4GB RAM
- 1GB disk space

### For Advanced Use (5+ tables, ML training)
- 8+ CPU cores
- 8GB+ RAM
- 2GB+ disk space
- GPU optional but helpful for ML

## Verification

After installation, verify your system meets requirements:

```bash
python scripts/start.py --self-test
```

This will check:
- ✓ Python version compatibility
- ✓ System dependencies installed
- ✓ Disk space availability
- ✓ Network connectivity
- ✓ Package conflicts
- ✓ Core functionality

## Troubleshooting

If requirements check fails, see [INSTALLATION_TROUBLESHOOTING.md](./INSTALLATION_TROUBLESHOOTING.md) for detailed solutions.
