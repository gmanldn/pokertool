# Installation Environment Variables

## Overview

These environment variables control installation behavior and can be set before running `python scripts/start.py`.

## Installation Control

### POKERTOOL_SKIP_CHECKS
**Type:** Boolean (1/0, true/false, yes/no)  
**Default:** `false`  
**Description:** Skip pre-installation checks (Python version, dependencies, disk space, network)  
**Usage:**
```bash
export POKERTOOL_SKIP_CHECKS=true
python scripts/start.py
```
**Warning:** Not recommended - may cause installation failures

### POKERTOOL_VERBOSE
**Type:** Boolean  
**Default:** `false`  
**Description:** Enable verbose installation output  
**Usage:**
```bash
export POKERTOOL_VERBOSE=true
python scripts/start.py
```
**Equivalent:** `python scripts/start.py -v`

### POKERTOOL_INSTALL_LOG
**Type:** File path  
**Default:** `~/.pokertool/install.log`  
**Description:** Location for installation log file  
**Usage:**
```bash
export POKERTOOL_INSTALL_LOG=/var/log/pokertool-install.log
python scripts/start.py
```

## Network Configuration

### HTTP_PROXY / HTTPS_PROXY
**Type:** URL  
**Default:** None  
**Description:** Proxy server for package downloads  
**Usage:**
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
python scripts/start.py
```

### PIP_INDEX_URL
**Type:** URL  
**Default:** `https://pypi.org/simple`  
**Description:** Alternative PyPI mirror  
**Usage:**
```bash
export PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
python scripts/start.py
```

### PIP_TIMEOUT
**Type:** Integer (seconds)  
**Default:** 60  
**Description:** Timeout for pip operations  
**Usage:**
```bash
export PIP_TIMEOUT=300
python scripts/start.py
```

## Application Configuration

### POKERTOOL_VERSION
**Type:** String  
**Default:** Auto-detected from VERSION file  
**Description:** Override version number  
**Usage:**
```bash
export POKERTOOL_VERSION=101.0.2
python scripts/start.py
```

### POKERTOOL_PORT
**Type:** Integer  
**Default:** 5001  
**Description:** Backend API server port  
**Usage:**
```bash
export POKERTOOL_PORT=8080
python scripts/start.py
```

### CHROME_REMOTE_DEBUGGING_PORT
**Type:** Integer  
**Default:** 9222  
**Description:** Chrome DevTools Protocol port  
**Usage:**
```bash
export CHROME_REMOTE_DEBUGGING_PORT=9223
python scripts/start.py
```

## Python Environment

### PYTHONPATH
**Type:** Directory path(s)  
**Default:** Auto-set by start.py  
**Description:** Python module search paths  
**Usage:**
```bash
export PYTHONPATH=/path/to/pokertool/src:$PYTHONPATH
python scripts/start.py
```

### VIRTUAL_ENV
**Type:** Directory path  
**Default:** `.venv` in project root  
**Description:** Virtual environment location  
**Usage:**
```bash
export VIRTUAL_ENV=/custom/venv/path
python scripts/start.py
```

## Development Options

### POKERTOOL_DEV_MODE
**Type:** Boolean  
**Default:** `false`  
**Description:** Enable development mode with hot reload  
**Usage:**
```bash
export POKERTOOL_DEV_MODE=true
python scripts/start.py
```

### POKERTOOL_DEBUG
**Type:** Boolean  
**Default:** `false`  
**Description:** Enable debug logging  
**Usage:**
```bash
export POKERTOOL_DEBUG=true
python scripts/start.py
```

### POKERTOOL_TEST_MODE
**Type:** Boolean  
**Default:** `false`  
**Description:** Run in test mode (uses test database, etc.)  
**Usage:**
```bash
export POKERTOOL_TEST_MODE=true
python scripts/start.py
```

## Frontend Configuration

### REACT_APP_API_URL
**Type:** URL  
**Default:** `http://127.0.0.1:5001`  
**Description:** Backend API endpoint for frontend  
**Auto-set:** By start.py based on POKERTOOL_PORT  

### REACT_APP_WS_URL
**Type:** URL  
**Default:** `ws://127.0.0.1:5001`  
**Description:** WebSocket endpoint for frontend  
**Auto-set:** By start.py based on POKERTOOL_PORT  

### REACT_APP_VERSION
**Type:** String  
**Default:** Auto-detected from VERSION file  
**Description:** Version displayed in frontend UI  
**Auto-set:** By start.py  

### NODE_ENV
**Type:** String (development/production)  
**Default:** `development`  
**Description:** Node.js environment mode  
**Usage:**
```bash
export NODE_ENV=production
npm start
```

## Platform-Specific

### macOS

#### OBJC_DISABLE_INITIALIZE_FORK_SAFETY
**Type:** Boolean (YES/NO)  
**Default:** Not set  
**Description:** Disable fork safety check in macOS (for pyobjc)  
**Usage:**
```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
python scripts/start.py
```

### Windows

#### PYTHONIOENCODING
**Type:** String  
**Default:** `utf-8`  
**Description:** Set Python I/O encoding  
**Usage:**
```cmd
set PYTHONIOENCODING=utf-8
python scripts\start.py
```

## Examples

### Behind Corporate Proxy
```bash
export HTTP_PROXY=http://proxy.corp.com:8080
export HTTPS_PROXY=http://proxy.corp.com:8080
export PIP_INDEX_URL=https://pypi.org/simple
export PIP_TIMEOUT=300
python scripts/start.py
```

### Development Setup
```bash
export POKERTOOL_DEV_MODE=true
export POKERTOOL_DEBUG=true
export POKERTOOL_VERBOSE=true
python scripts/start.py
```

### Custom Ports
```bash
export POKERTOOL_PORT=8080
export CHROME_REMOTE_DEBUGGING_PORT=9223
python scripts/start.py
```

### Clean Install
```bash
unset POKERTOOL_SKIP_CHECKS
export POKERTOOL_VERBOSE=true
rm -rf .venv pokertool-frontend/node_modules
python scripts/start.py --setup-only
```

## Persistence

To make environment variables permanent:

### Unix (Bash)
Add to `~/.bashrc` or `~/.bash_profile`:
```bash
export POKERTOOL_PORT=8080
export POKERTOOL_DEBUG=true
```

### Unix (Zsh)
Add to `~/.zshrc`:
```bash
export POKERTOOL_PORT=8080
export POKERTOOL_DEBUG=true
```

### Windows (PowerShell)
Add to PowerShell profile:
```powershell
$env:POKERTOOL_PORT = "8080"
$env:POKERTOOL_DEBUG = "true"
```

Or set system-wide via System Properties > Environment Variables

## See Also

- [Installation Requirements](./INSTALLATION_REQUIREMENTS.md)
- [Troubleshooting Guide](./INSTALLATION_TROUBLESHOOTING.md)
- [Configuration Guide](./CONFIGURATION.md)
