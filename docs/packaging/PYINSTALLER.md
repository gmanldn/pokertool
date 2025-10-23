# PyInstaller Packaging Guide

## Overview

This guide covers creating standalone executable packages for PokerTool using PyInstaller, enabling distribution on Windows, macOS, and Linux without requiring Python installation.

## What is PyInstaller?

PyInstaller bundles Python applications into standalone executables that include:
- Python interpreter
- Application code
- Dependencies and libraries
- Data files and assets
- Icon and branding

Users can run the application without installing Python or dependencies.

## Installation

```bash
# Install PyInstaller
pip install pyinstaller

# Or install from requirements
pip install -r requirements-packaging.txt

# Verify installation
pyinstaller --version
```

## Basic Usage

### Simple Build

```bash
# Basic executable
pyinstaller src/main.py

# Single file executable
pyinstaller --onefile src/main.py

# With custom name
pyinstaller --onefile --name pokertool src/main.py
```

### GUI Application

```bash
# GUI app (no console window)
pyinstaller --onefile --windowed src/main.py

# With icon
pyinstaller --onefile --windowed --icon=assets/pokertool-icon.ico src/main.py
```

## Spec File Configuration

Create `pokertool.spec` for advanced configuration:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Analysis - find all dependencies
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('assets', 'assets'),
        ('model_calibration_data', 'model_calibration_data'),
        ('ranges', 'ranges'),
    ],
    hiddenimports=[
        'pkg_resources.py2_warn',
        'sklearn.utils._cython_blas',
        'sklearn.neighbors.typedefs',
        'sklearn.neighbors.quad_tree',
        'sklearn.tree._utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'test',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Process data files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PokerTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app - no console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/pokertool-icon.ico'  # Windows
)

# macOS-specific bundle
app = BUNDLE(
    exe,
    name='PokerTool.app',
    icon='assets/pokertool-icon.icns',  # macOS
    bundle_identifier='com.pokertool.app',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1.0.0',
    },
)
```

### Build with Spec File

```bash
# Build using spec file
pyinstaller pokertool.spec

# Clean build
pyinstaller --clean pokertool.spec

# Output to specific directory
pyinstaller --distpath ./dist pokertool.spec
```

## Platform-Specific Configuration

### Windows

```python
# pokertool-windows.spec
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='PokerTool.exe',
    icon='assets/pokertool-icon.ico',
    console=False,  # No console window
    uac_admin=False,  # Don't require admin
    version='version_info.txt',  # Version information
)
```

#### Version Information (Windows)

Create `version_info.txt`:

```python
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'PokerTool'),
        StringStruct(u'FileDescription', u'AI-Powered Poker Analysis Tool'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'PokerTool'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 PokerTool'),
        StringStruct(u'OriginalFilename', u'PokerTool.exe'),
        StringStruct(u'ProductName', u'PokerTool'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

### macOS

```python
# pokertool-macos.spec
app = BUNDLE(
    exe,
    name='PokerTool.app',
    icon='assets/pokertool-icon.icns',
    bundle_identifier='com.pokertool.app',
    info_plist={
        'CFBundleName': 'PokerTool',
        'CFBundleDisplayName': 'PokerTool',
        'CFBundleGetInfoString': "AI-Powered Poker Analysis",
        'CFBundleIdentifier': 'com.pokertool.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2025 PokerTool',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
    },
)
```

### Linux

```python
# pokertool-linux.spec
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='pokertool',
    debug=False,
    strip=True,  # Strip debug symbols
    upx=True,  # Compress with UPX
    console=False,
)
```

## Including Data Files

### Add Files and Folders

```python
# In spec file
datas=[
    ('config/*.json', 'config'),
    ('assets/icons/*.png', 'assets/icons'),
    ('model_calibration_data', 'model_calibration_data'),
    ('README.md', '.'),
],
```

### Access Data Files at Runtime

```python
import os
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Usage
config_path = resource_path('config/poker_config.json')
icon_path = resource_path('assets/icons/card.png')
```

## Hidden Imports

### Common Hidden Imports

```python
hiddenimports=[
    # scikit-learn
    'sklearn.utils._cython_blas',
    'sklearn.neighbors.typedefs',
    'sklearn.neighbors.quad_tree',
    'sklearn.tree._utils',
    
    # pandas
    'pandas._libs.tslibs.timedeltas',
    
    # numpy
    'numpy.core._methods',
    'numpy.lib.format',
    
    # Other
    'pkg_resources.py2_warn',
    'win32timezone',  # Windows only
],
```

### Find Missing Imports

```bash
# Run and check for import errors
./dist/pokertool

# Use --debug all for verbose output
pyinstaller --debug all pokertool.spec
```

## Optimization

### Reduce Size

```python
# Exclude unnecessary modules
excludes=[
    'matplotlib',
    'tkinter',
    'test',
    'unittest',
    'email',
    'html',
    'http',
    'urllib',
    'xml',
    'pydoc',
],

# Use UPX compression
exe = EXE(
    ...
    upx=True,
    upx_exclude=['vcruntime140.dll'],  # Don't compress critical DLLs
)

# Strip debug symbols (Linux)
strip=True,
```

### One-File vs One-Folder

**One-File** (`--onefile`):
- Single executable file
- Slower startup (extracts to temp)
- Simpler distribution
- ~100-200MB

**One-Folder** (default):
- Folder with executable and dependencies
- Faster startup
- Larger distribution package
- Easier to debug

```bash
# One-file build
pyinstaller --onefile pokertool.spec

# One-folder build (default)
pyinstaller pokertool.spec
```

## Code Signing

### Windows Code Signing

```bash
# Sign executable with SignTool
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com /v dist/PokerTool.exe

# Or use PyInstaller with codesign
pyinstaller --codesign-identity "Developer ID" pokertool.spec
```

### macOS Code Signing

```bash
# Sign application
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/PokerTool.app

# Verify signature
codesign --verify --verbose dist/PokerTool.app

# Notarize with Apple
xcrun altool --notarize-app --file PokerTool.app.zip \
  --primary-bundle-id com.pokertool.app \
  --username your@email.com \
  --password app-specific-password
```

### Linux (Optional)

```bash
# GPG sign the binary
gpg --detach-sign --armor dist/pokertool

# Verify
gpg --verify dist/pokertool.asc dist/pokertool
```

## Testing

### Test Checklist

```bash
# 1. Build the application
pyinstaller --clean pokertool.spec

# 2. Test on clean system
# - No Python installed
# - No dependencies installed

# 3. Test all features
# - Start application
# - Load configuration
# - Test core functionality
# - Check file access
# - Verify networking

# 4. Check file size
ls -lh dist/PokerTool*

# 5. Test error handling
# - Invalid config
# - Missing files
# - Network errors
```

### Automated Testing

```python
# test_package.py
import subprocess
import sys
import os

def test_executable():
    exe_path = 'dist/PokerTool.exe' if sys.platform == 'win32' else 'dist/PokerTool'
    
    # Check file exists
    assert os.path.exists(exe_path), f"Executable not found: {exe_path}"
    
    # Check file size
    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    assert size_mb < 200, f"Executable too large: {size_mb:.1f}MB"
    
    # Test execution
    result = subprocess.run([exe_path, '--version'], capture_output=True, timeout=10)
    assert result.returncode == 0, "Executable failed to run"
    
    print("✓ All tests passed")

if __name__ == '__main__':
    test_executable()
```

## Build Scripts

### Cross-Platform Build Script

```bash
#!/bin/bash
# build.sh

set -e

echo "Building PokerTool with PyInstaller..."

# Clean previous builds
rm -rf build dist

# Determine platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    SPEC="pokertool-macos.spec"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    SPEC="pokertool-windows.spec"
else
    SPEC="pokertool-linux.spec"
fi

# Build
pyinstaller --clean --noconfirm "$SPEC"

# Test
python test_package.py

echo "Build complete!"
```

### Windows Build Script

```powershell
# build.ps1
$ErrorActionPreference = "Stop"

Write-Host "Building PokerTool for Windows..."

# Clean
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# Build
pyinstaller --clean --noconfirm pokertool-windows.spec

# Sign (if certificate available)
if (Test-Path "certificate.pfx") {
    signtool sign /f certificate.pfx /p $env:CERT_PASSWORD dist/PokerTool.exe
}

# Test
python test_package.py

Write-Host "Build complete!"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build executable
        run: pyinstaller --clean pokertool-windows.spec
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: PokerTool-Windows
          path: dist/PokerTool.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build executable
        run: pyinstaller --clean pokertool-macos.spec
      
      - name: Create DMG
        run: |
          brew install create-dmg
          create-dmg --volname "PokerTool" \
            --window-pos 200 120 --window-size 600 400 \
            --icon-size 100 --app-drop-link 400 185 \
            dist/PokerTool.dmg dist/PokerTool.app
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: PokerTool-macOS
          path: dist/PokerTool.dmg

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build executable
        run: pyinstaller --clean pokertool-linux.spec
      
      - name: Create tarball
        run: |
          cd dist
          tar czf PokerTool-Linux.tar.gz pokertool
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: PokerTool-Linux
          path: dist/PokerTool-Linux.tar.gz
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Find missing imports
pyinstaller --debug imports pokertool.spec
```

#### File Not Found
```python
# Use resource_path function
config = load_config(resource_path('config/default.json'))
```

#### Slow Startup (One-File)
```bash
# Use one-folder instead
pyinstaller pokertool.spec  # Without --onefile
```

#### Large File Size
```python
# Exclude unnecessary modules
excludes=['matplotlib', 'tkinter', 'test', 'unittest']

# Use UPX compression
upx=True
```

### Debug Mode

```bash
# Run with debug output
pyinstaller --debug all pokertool.spec

# Check what's included
pyi-archive_viewer dist/PokerTool.exe
```

## Best Practices

1. **Test on clean systems** - No Python or dependencies
2. **Use spec files** - Better control than command line
3. **Code sign** - Required for distribution
4. **Minimize size** - Exclude unnecessary modules
5. **Test thoroughly** - All features and edge cases
6. **Version control spec** - Track changes to build config
7. **Automate builds** - Use CI/CD pipelines
8. **Document dependencies** - List all required libraries

## Next Steps

- Review [Electron Packaging](ELECTRON.md)
- Consider [Tauri Alternative](TAURI.md)
- Explore [Native Installers](NATIVE_INSTALLERS.md)
- Set up [Auto-Updater](../features/AUTO_UPDATER.md)

## References

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller Spec Files](https://pyinstaller.org/en/stable/spec-files.html)
- [Hooks and Runtime Hooks](https://pyinstaller.org/en/stable/hooks.html)
- [Code Signing Guide](https://pyinstaller.org/en/stable/usage.html#code-signing)
