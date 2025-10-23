# Installation Troubleshooting Guide

## Quick Diagnostic

Run the built-in diagnostic:
```bash
python scripts/start.py --self-test
```

Check installation logs:
```bash
cat ~/.pokertool/install.log
```

## Common Installation Errors

### Python Version Issues

#### Error: "Python 3.X is too old"
**Cause:** Python version < 3.9  
**Solution:**
```bash
# macOS
brew install python@3.12

# Ubuntu/Debian
sudo apt-get install python3.12 python3.12-venv

# Windows
# Download from https://www.python.org/downloads/
```

#### Error: "ImportError: No module named 'venv'"
**Cause:** Python venv module not installed  
**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# Other systems
pip install virtualenv
```

### System Dependencies Missing

#### Error: "git not found" / "node not found" / "npm not found"
**Cause:** Required system tools not installed  
**Solution:**
```bash
# macOS
brew install git node

# Ubuntu/Debian
sudo apt-get install git nodejs npm

# Windows
# Install from official websites:
# - Git: https://git-scm.com/download/win
# - Node.js: https://nodejs.org/
```

### Disk Space Issues

#### Error: "Insufficient disk space"
**Cause:** Less than 500MB free space  
**Solution:**
1. Free up disk space
2. Check with: `df -h` (Unix) or `wmic logicaldisk get size,freespace` (Windows)
3. Consider installing on different drive

### Network Issues

#### Error: "Could not fetch packages"
**Cause:** Network connectivity issues or firewall  
**Solutions:**
1. Check internet connection
2. Try alternative PyPI mirror:
   ```bash
   pip install -r requirements.txt --index-url https://pypi.tuna.tsinghua.edu.cn/simple
   ```
3. Configure proxy if behind corporate firewall:
   ```bash
   export HTTP_PROXY=http://proxy.example.com:8080
   export HTTPS_PROXY=http://proxy.example.com:8080
   pip install -r requirements.txt
   ```

#### Error: "Connection timeout"
**Cause:** Slow or unstable connection  
**Solution:**
```bash
pip install -r requirements.txt --timeout 300  # 5 minute timeout
```

### Package Conflicts

#### Error: "opencv-python conflicts with opencv-python-headless"
**Cause:** Both versions installed  
**Solution:**
```bash
pip uninstall opencv-python opencv-python-headless
pip install opencv-python-headless  # Preferred version
```

#### Error: "Pillow conflicts with PIL"
**Cause:** Both PIL and Pillow installed  
**Solution:**
```bash
pip uninstall PIL Pillow
pip install Pillow
```

### Compilation Errors

#### Error: "error: Microsoft Visual C++ 14.0 or greater is required"
**Cause:** Missing C++ compiler on Windows  
**Solution:**
1. Install Visual Studio Build Tools
2. Or install pre-built wheels:
   ```bash
   pip install --only-binary :all: package-name
   ```

#### Error: "xcrun: error: invalid active developer path"
**Cause:** Xcode command line tools missing (macOS)  
**Solution:**
```bash
xcode-select --install
```

### Permission Errors

#### Error: "Permission denied"
**Cause:** Insufficient permissions  
**Solution:**
```bash
# Don't use sudo pip!
# Use virtual environment instead:
python -m venv .venv
source .venv/bin/activate  # Unix
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Frontend Installation Issues

#### Error: "npm install failed"
**Cause:** Node version incompatibility or corrupted cache  
**Solutions:**
```bash
# Clear npm cache
npm cache clean --force

# Update npm
npm install -g npm@latest

# Use specific Node version
nvm install 18
nvm use 18
npm install
```

#### Error: "EACCES: permission denied"
**Cause:** Global npm permissions issue  
**Solution:**
```bash
# Fix npm permissions (Unix)
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

### Virtual Environment Issues

#### Error: "venv activation fails"
**Cause:** Shell-specific activation script  
**Solutions:**
```bash
# Bash/Zsh
source .venv/bin/activate

# Fish
source .venv/bin/activate.fish

# Windows CMD
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

#### Error: "PowerShell script execution disabled"
**Cause:** PowerShell execution policy  
**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Platform-Specific Issues

### macOS Issues

#### Error: "SSL: CERTIFICATE_VERIFY_FAILED"
**Cause:** Python SSL certificates not installed  
**Solution:**
```bash
# Run Python certificate installer
/Applications/Python\ 3.12/Install\ Certificates.command
```

#### Error: "Port 5000 already in use"
**Cause:** macOS Control Center uses port 5000  
**Solution:** App automatically uses port 5001, no action needed

### Linux Issues

#### Error: "libpython3.X.so.1.0: cannot open shared object file"
**Cause:** Python shared library not in LD_LIBRARY_PATH  
**Solution:**
```bash
# Add to ~/.bashrc
export LD_LIBRARY_PATH=/usr/lib/python3.12:$LD_LIBRARY_PATH
```

#### Error: "No module named '_ctypes'"
**Cause:** libffi-dev not installed  
**Solution:**
```bash
sudo apt-get install libffi-dev
# Rebuild Python if necessary
```

### Windows Issues

#### Error: "long path not enabled"
**Cause:** Windows long path limitation  
**Solution:**
1. Run as Administrator:
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```
2. Or install in shorter path

## Advanced Troubleshooting

### Clean Install
```bash
# Remove existing installation
rm -rf .venv pokertool-frontend/node_modules

# Clear caches
pip cache purge
npm cache clean --force

# Reinstall
python scripts/start.py --setup-only
```

### Verbose Installation
```bash
# Enable verbose output
python scripts/start.py -v --setup-only

# Check logs
cat ~/.pokertool/install.log
```

### Test Specific Components
```bash
# Test Python environment
python -c "import sys; print(sys.version); print(sys.executable)"

# Test pip
pip --version

# Test Node/npm
node --version
npm --version

# Test imports
python -c "import numpy, PIL, cv2, fastapi"
```

### Check for Stuck Processes
```bash
# Unix
ps aux | grep pokertool
lsof -i :5001
lsof -i :3000

# Windows
tasklist | findstr python
netstat -ano | findstr :5001
netstat -ano | findstr :3000
```

## Getting Help

If you're still experiencing issues:

1. **Check existing issues:** https://github.com/gmanldn/pokertool/issues
2. **Create new issue with:**
   - Operating system and version
   - Python version (`python --version`)
   - Error message (full traceback)
   - Installation logs (~/.pokertool/install.log)
   - Output of: `python scripts/start.py --self-test`

3. **Community support:**
   - Discord: [Coming soon]
   - Discussions: https://github.com/gmanldn/pokertool/discussions

## Quick Fixes Checklist

- [ ] Run with latest Python 3.12
- [ ] Clear all caches (pip, npm)
- [ ] Check disk space (>500MB free)
- [ ] Verify internet connection
- [ ] Install in virtual environment (not system-wide)
- [ ] Run as regular user (not root/Administrator)
- [ ] Check firewall/antivirus settings
- [ ] Use short installation path (<100 characters)
- [ ] Close other pokertool instances
- [ ] Restart computer after system package installation
