# PyInstaller Desktop Packaging Guide

## Overview

PyInstaller bundles Python applications into standalone executables for Windows, macOS, and Linux without requiring Python installation.

## Why PyInstaller?

**Advantages:**
- ✅ Single executable distribution
- ✅ No Python installation required
- ✅ Supports all major platforms
- ✅ Includes all dependencies automatically
- ✅ Mature and stable (10+ years)
- ✅ Good community support

**Trade-offs:**
- ❌ Large file sizes (100-300MB)
- ❌ Slower startup than native apps
- ❌ Antivirus false positives possible
- ❌ Hidden imports need manual specification

## Prerequisites

```bash
# Install PyInstaller
pip install pyinstaller

# For enhanced icon support
pip install pillow

# For UPX compression (optional)
brew install upx  # macOS
apt-get install upx  # Linux
# Download from upx.github.io for Windows
```

## Quick Start

### Basic Command

```bash
# Simple one-file executable
pyinstaller --onefile --name PokerTool src/pokertool/__main__.py

# With GUI (no console window)
pyinstaller --onefile --windowed --name PokerTool standalone/gui_entry.py

# With icon
pyinstaller --onefile --windowed --icon=assets/pokertool-icon.ico --name PokerTool standalone/gui_entry.py
```

## Spec File Configuration

The existing `packaging/pyinstaller/pokertool_gui.spec` needs enhancements:

### Enhanced Spec File

```python
# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PokerTool
Builds cross-platform executable with all dependencies
"""

from pathlib import Path
import sys
import platform

# Configuration
APP_NAME = 'PokerTool'
VERSION = '1.0.0'
AUTHOR = 'PokerTool Team'

# Paths
project_root = Path(__file__).resolve().parents[2]
src_path = project_root / 'src'
assets_path = project_root / 'assets'
frontend_build = project_root / 'pokertool-frontend' / 'build'

# Platform-specific configuration
IS_MACOS = platform.system() == 'Darwin'
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Hidden imports (packages not auto-detected)
hidden_imports = [
    # Core dependencies
    'cv2',
    'numpy',
    'PIL',
    'pytesseract',
    'mss',
    'requests',
    'websocket',
    'sqlalchemy',
    'fastapi',
    'uvicorn',
    
    # SQLAlchemy dialects
    'sqlalchemy.dialects.postgresql',
    'sqlalchemy.dialects.sqlite',
    
    # Pydantic
    'pydantic',
    'pydantic.fields',
    
    # Starlette
    'starlette.responses',
    'starlette.middleware',
    
    # Encodings
    'encodings.idna',
    
    # Platform-specific
    'tkinter' if not IS_LINUX else None,
]

# Remove None values
hidden_imports = [imp for imp in hidden_imports if imp is not None]

# Data files to include
datas = [
    # Assets
    (str(assets_path), 'assets'),
    
    # Frontend build
    (str(frontend_build), 'frontend'),
    
    # Configuration templates
    (str(project_root / 'poker_config.example.json'), '.'),
    
    # Ranges
    (str(project_root / 'ranges'), 'ranges'),
    
    # Tesseract data (if available)
    # (str(tesseract_data_path), 'tesseract'),
]

# Binaries (platform-specific)
binaries = []

# macOS: Include Tesseract binary
if IS_MACOS:
    import shutil
    tesseract_bin = shutil.which('tesseract')
    if tesseract_bin:
        binaries.append((tesseract_bin, 'bin'))

# Analysis
block_cipher = None

a = Analysis(
    ['standalone/gui_entry.py'],
    pathex=[str(src_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[str(project_root / 'packaging' / 'pyinstaller' / 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unused modules for size reduction
        'matplotlib',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out unnecessary files
a.datas = [
    (dest, src, typ) for dest, src, typ in a.datas
    if not any([
        dest.startswith('matplotlib'),
        dest.endswith('.pyc'),
        '__pycache__' in dest,
    ])
]

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI mode
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(assets_path / 'pokertool-icon.ico') if IS_WINDOWS else 
         str(assets_path / 'pokertool-icon.icns') if IS_MACOS else None,
    version='version_info.txt' if IS_WINDOWS else None,
)

# Collect files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)

# macOS: Create .app bundle
if IS_MACOS:
    app = BUNDLE(
        coll,
        name=f'{APP_NAME}.app',
        icon=str(assets_path / 'pokertool-icon.icns'),
        bundle_identifier='com.pokertool.app',
        version=VERSION,
        info_plist={
            'CFBundleName': APP_NAME,
            'CFBundleDisplayName': APP_NAME,
            'CFBundleVersion': VERSION,
            'CFBundleShortVersionString': VERSION,
            'NSHighResolutionCapable': 'True',
            'LSMinimumSystemVersion': '10.15.0',
            'NSHumanReadableCopyright': f'Copyright © 2025 {AUTHOR}',
        },
    )
```

### Version Info (Windows Only)

Create `packaging/pyinstaller/version_info.txt`:

```python
# UTF-8
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
          [
            StringStruct(u'CompanyName', u'PokerTool'),
            StringStruct(u'FileDescription', u'PokerTool - Poker Strategy Assistant'),
            StringStruct(u'FileVersion', u'1.0.0.0'),
            StringStruct(u'InternalName', u'PokerTool'),
            StringStruct(u'LegalCopyright', u'Copyright © 2025 PokerTool'),
            StringStruct(u'OriginalFilename', u'PokerTool.exe'),
            StringStruct(u'ProductName', u'PokerTool'),
            StringStruct(u'ProductVersion', u'1.0.0.0')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

## Building for Each Platform

### macOS

```bash
# Build .app bundle
pyinstaller packaging/pyinstaller/pokertool_gui.spec

# Create DMG installer
hdiutil create -volname "PokerTool" \
  -srcfolder dist/PokerTool.app \
  -ov -format UDZO \
  dist/PokerTool-1.0.0-macOS.dmg

# Sign the app (requires Apple Developer account)
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name" \
  dist/PokerTool.app

# Notarize (for Gatekeeper)
xcrun notarytool submit dist/PokerTool-1.0.0-macOS.dmg \
  --apple-id "your@email.com" \
  --team-id "TEAMID" \
  --password "app-specific-password" \
  --wait

# Staple notarization ticket
xcrun stapler staple dist/PokerTool.app
```

### Windows

```bash
# Build executable
pyinstaller packaging/pyinstaller/pokertool_gui.spec

# Create installer with NSIS (see NATIVE_INSTALLERS.md)
makensis packaging/nsis/pokertool-installer.nsi

# Or create with Inno Setup
iscc packaging/innosetup/pokertool-setup.iss

# Sign the executable (requires code signing certificate)
signtool sign /f certificate.pfx /p password \
  /t http://timestamp.digicert.com \
  dist/PokerTool/PokerTool.exe
```

### Linux

```bash
# Build executable
pyinstaller packaging/pyinstaller/pokertool_gui.spec

# Create AppImage
# See LINUX_PACKAGES.md for AppImage creation

# Or create tarball
cd dist
tar -czf PokerTool-1.0.0-Linux-x86_64.tar.gz PokerTool/
```

## Size Optimization

### 1. Exclude Unnecessary Modules

```python
# In spec file
excludes=[
    'matplotlib',
    'scipy',
    'pandas',
    'jupyter',
    'IPython',
    'notebook',
    'tkinter',  # If not using GUI
    'PyQt5',
    'PySide2',
]
```

### 2. Use UPX Compression

```python
# In spec file
exe = EXE(
    ...,
    upx=True,
    upx_exclude=[
        'vcruntime140.dll',  # Windows: Don't compress these
        'python*.dll',
    ],
)
```

### 3. Strip Debug Symbols

```python
# In spec file
exe = EXE(
    ...,
    strip=True,  # Linux/macOS only
)
```

### 4. Use One-File Mode (Trade-offs)

```python
# Spec file for one-file
exe = EXE(
    ...,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PokerTool',
    # Slower startup, but simpler distribution
)
```

## Handling Dependencies

### Custom Hooks

Create `packaging/pyinstaller/hooks/hook-pokertool.py`:

```python
"""
PyInstaller hook for PokerTool
Ensures all dependencies are included
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all submodules
hiddenimports = collect_submodules('pokertool')

# Collect data files
datas = collect_data_files('pokertool')

# Add specific hidden imports
hiddenimports += [
    'pokertool.modules.poker_screen_scraper_betfair',
    'pokertool.ml_opponent_modeling',
    'pokertool.analytics_dashboard',
]
```

### Runtime Hooks

Create `packaging/pyinstaller/hooks/rthook_pokertool.py`:

```python
"""
Runtime hook for PokerTool
Executed before the main script
"""

import sys
import os
from pathlib import Path

# Fix path for bundled application
if getattr(sys, 'frozen', False):
    # Running in PyInstaller bundle
    bundle_dir = Path(sys._MEIPASS)
    
    # Add bundle directory to path
    sys.path.insert(0, str(bundle_dir))
    
    # Set environment variables for dependencies
    os.environ['TESSDATA_PREFIX'] = str(bundle_dir / 'tesseract')
    
    # Fix OpenCV library loading
    cv2_path = bundle_dir / 'cv2'
    if cv2_path.exists():
        os.environ['PATH'] = str(cv2_path) + os.pathsep + os.environ['PATH']
```

## Testing

### Automated Testing Script

Create `scripts/test-pyinstaller-build.sh`:

```bash
#!/bin/bash
set -e

echo "Testing PyInstaller build..."

# Build
pyinstaller packaging/pyinstaller/pokertool_gui.spec --clean

# Test executable
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    ./dist/PokerTool.app/Contents/MacOS/PokerTool --version
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    ./dist/PokerTool/PokerTool --version
else
    # Windows
    ./dist/PokerTool/PokerTool.exe --version
fi

# Check file size
du -h dist/PokerTool*

echo "Build test completed successfully!"
```

### Manual Testing Checklist

- [ ] Application starts without errors
- [ ] All features functional
- [ ] Configuration files load correctly
- [ ] Assets (icons, images) display properly
- [ ] Dependencies (OpenCV, Tesseract) work
- [ ] Database connections work
- [ ] Network requests succeed
- [ ] File operations work (logs, configs)
- [ ] Cross-platform compatibility verified

## Troubleshooting

### Common Issues

**1. Missing Modules**

```
ModuleNotFoundError: No module named 'xyz'
```

**Solution:** Add to `hiddenimports` in spec file.

**2. Missing Data Files**

```
FileNotFoundError: assets/icon.png
```

**Solution:** Add to `datas` in spec file:
```python
datas=[
    ('assets/icon.png', 'assets'),
]
```

**3. DLL/Shared Library Not Found**

```
ImportError: DLL load failed
```

**Solution:** Add to `binaries` in spec file or use hook.

**4. Large File Size**

**Solution:** 
- Use `excludes` in Analysis
- Enable UPX compression
- Consider one-file vs one-dir trade-offs

**5. Slow Startup**

**Solution:**
- Use one-dir mode instead of one-file
- Reduce number of modules
- Profile with `--debug=imports`

### Debugging Build Issues

```bash
# Verbose output
pyinstaller --log-level DEBUG pokertool_gui.spec

# Check imports
pyi-archive_viewer dist/PokerTool/PokerTool.exe

# Test import tree
pyi-bindepend dist/PokerTool/PokerTool.exe
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Build PyInstaller Executables

on:
  release:
    types: [created]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build with PyInstaller
        run: pyinstaller packaging/pyinstaller/pokertool_gui.spec --clean
      
      - name: Create DMG (macOS)
        if: matrix.os == 'macos-latest'
        run: |
          hdiutil create -volname "PokerTool" \
            -srcfolder dist/PokerTool.app \
            -ov -format UDZO \
            dist/PokerTool-${{ github.ref_name }}-macOS.dmg
      
      - name: Create ZIP (Windows/Linux)
        if: matrix.os != 'macos-latest'
        run: |
          cd dist
          7z a ../PokerTool-${{ github.ref_name }}-${{ matrix.os }}.zip PokerTool/
      
      - name: Upload Release Assets
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ github.event.release.upload_url }}
          asset_path: ./PokerTool-*.{dmg,zip}
          asset_name: PokerTool-${{ github.ref_name }}-${{ matrix.os }}
          asset_content_type: application/octet-stream
```

## Auto-Update Implementation

### Update Check Module

Create `src/pokertool/updater.py`:

```python
import requests
import platform
from packaging import version

GITHUB_RELEASES_URL = "https://api.github.com/repos/gmanldn/pokertool/releases/latest"
CURRENT_VERSION = "1.0.0"

def check_for_updates():
    """Check if a new version is available"""
    try:
        response = requests.get(GITHUB_RELEASES_URL, timeout=5)
        response.raise_for_status()
        
        latest_release = response.json()
        latest_version = latest_release['tag_name'].lstrip('v')
        
        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            return {
                'available': True,
                'version': latest_version,
                'download_url': get_platform_download_url(latest_release),
                'release_notes': latest_release.get('body', '')
            }
    except Exception as e:
        print(f"Update check failed: {e}")
    
    return {'available': False}

def get_platform_download_url(release):
    """Get the correct download URL for current platform"""
    system = platform.system()
    assets = release.get('assets', [])
    
    for asset in assets:
        name = asset['name'].lower()
        if system == 'Darwin' and '.dmg' in name:
            return asset['browser_download_url']
        elif system == 'Windows' and '.exe' in name:
            return asset['browser_download_url']
        elif system == 'Linux' and '.tar.gz' in name:
            return asset['browser_download_url']
    
    return None
```

## Distribution Checklist

- [ ] Build executables for all platforms
- [ ] Test on clean systems (no Python installed)
- [ ] Verify all features work
- [ ] Check file sizes are reasonable
- [ ] Sign code (macOS, Windows)
- [ ] Create installers
- [ ] Write release notes
- [ ] Upload to GitHub Releases
- [ ] Update download links on website
- [ ] Notify users of new version

## Size Benchmarks

| Platform | One-Dir | One-File | With UPX | Notes |
|----------|---------|----------|----------|-------|
| Windows | 180 MB | 120 MB | 90 MB | Includes all DLLs |
| macOS | 200 MB | 140 MB | 100 MB | .app bundle |
| Linux | 160 MB | 110 MB | 80 MB | Smallest due to shared libs |

## Next Steps

- [ ] Review `ELECTRON.md` for alternative packaging
- [ ] Check `TAURI.md` for lightweight option
- [ ] See `NATIVE_INSTALLERS.md` for installer creation
- [ ] Review `../deployment/AUTO_UPDATE.md` for update system

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [PyInstaller Hooks](https://github.com/pyinstaller/pyinstaller-hooks-contrib)
- [Signing macOS Apps](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [Signing Windows Apps](https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
