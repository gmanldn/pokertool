# Packaging Documentation

## Overview

This directory contains comprehensive guides for packaging PokerTool as standalone desktop applications for Windows, macOS, and Linux. Choose the approach that best fits your distribution requirements.

## Available Guides

### Desktop Packaging

1. **[PYINSTALLER.md](PYINSTALLER.md)** ⭐ **RECOMMENDED**
   - Bundle Python app into standalone executables
   - Supports Windows, macOS, and Linux
   - No Python installation required for users
   - Current spec file exists at `packaging/pyinstaller/pokertool_gui.spec`
   - **Best for:** Most users, traditional desktop distribution

2. **[TAURI.md](TAURI.md)** 🚀 **LIGHTWEIGHT**
   - Modern Rust-based framework (10-30MB binaries)
   - Native performance with web frontend
   - Auto-updater built-in
   - **Best for:** Modern desktop apps, smallest file size

3. **[ELECTRON.md](ELECTRON.md)** 💻 **FULL-FEATURED**
   - Complete desktop app framework
   - Extensive ecosystem and tooling
   - System tray, native menus
   - **Best for:** Feature-rich desktop apps, familiar stack

### Native Installers

4. **[NATIVE_INSTALLERS.md](NATIVE_INSTALLERS.md)**
   - Platform-specific installer creation
   - DMG/PKG for macOS
   - MSI/EXE for Windows  
   - DEB/RPM/AppImage for Linux
   - **Best for:** Professional distribution, app stores

### Linux Distribution

5. **[LINUX_PACKAGES.md](LINUX_PACKAGES.md)**
   - Flatpak packaging and Flathub submission
   - Snap packaging and Snapcraft store
   - AUR package for Arch Linux
   - **Best for:** Linux app stores, sandboxed distribution

### Package Managers

6. **[HOMEBREW.md](HOMEBREW.md)**
   - Homebrew formula for macOS/Linux
   - Custom tap or homebrew-core submission
   - **Best for:** Developer-friendly macOS distribution

7. **[WINGET.md](WINGET.md)**
   - Windows Package Manager manifest
   - Official Microsoft distribution channel
   - **Best for:** Windows 10/11 users

8. **[CHOCOLATEY.md](CHOCOLATEY.md)**
   - Chocolatey package for Windows
   - Popular with Windows power users
   - **Best for:** Windows automated deployments

## Quick Comparison

| Method | Size | Setup | Auto-Update | Best For |
|--------|------|-------|-------------|----------|
| PyInstaller | 100-300MB | Medium | Manual | Traditional apps |
| Tauri | 10-30MB | High | ✅ Built-in | Modern, lightweight |
| Electron | 80-150MB | Medium | ✅ Built-in | Feature-rich |
| Flatpak | 50-100MB | Medium | ✅ Built-in | Linux, sandboxed |
| Snap | 50-100MB | Medium | ✅ Built-in | Linux, all distros |
| Homebrew | N/A | Low | ✅ Built-in | macOS developers |
| Winget | N/A | Low | ✅ Built-in | Windows 10/11 |

## Getting Started

### 1. Choose Your Approach

**For Maximum Compatibility:**
```bash
# Use PyInstaller - works everywhere
pyinstaller packaging/pyinstaller/pokertool_gui.spec
```

**For Smallest Size:**
```bash
# Use Tauri - 90% smaller than alternatives
cd packaging/tauri
npm install
npm run tauri build
```

**For Feature-Rich Desktop:**
```bash
# Use Electron - most ecosystem support
cd packaging/electron
npm install
npm run build
```

### 2. Build for Your Platform

#### macOS
```bash
# PyInstaller - Creates .app bundle
pyinstaller packaging/pyinstaller/pokertool_gui.spec

# Create DMG installer
hdiutil create -volname "PokerTool" \
  -srcfolder dist/PokerTool.app \
  -ov -format UDZO \
  dist/PokerTool-1.0.0-macOS.dmg

# Sign and notarize (requires Apple Developer account)
codesign --deep --force --sign "Developer ID" dist/PokerTool.app
xcrun notarytool submit dist/PokerTool-1.0.0-macOS.dmg --wait
xcrun stapler staple dist/PokerTool.app
```

#### Windows
```bash
# PyInstaller - Creates .exe
pyinstaller packaging/pyinstaller/pokertool_gui.spec

# Create installer with NSIS
makensis packaging/nsis/pokertool-installer.nsi

# Sign executable (requires code signing certificate)
signtool sign /f certificate.pfx /p password dist/PokerTool.exe
```

#### Linux
```bash
# PyInstaller - Creates binary
pyinstaller packaging/pyinstaller/pokertool_gui.spec

# Create AppImage
appimagetool dist/PokerTool dist/PokerTool-x86_64.AppImage

# Or create Flatpak
flatpak-builder build packaging/flatpak/com.pokertool.PokerTool.yml
```

### 3. Distribute

- **GitHub Releases:** Upload binaries for direct download
- **App Stores:** Submit to Mac App Store, Microsoft Store, Flathub
- **Package Managers:** Publish to Homebrew, Winget, Chocolatey
- **Website:** Host downloads on pokertool.io

## Architecture Overview

### PyInstaller Build Process

```
┌─────────────────────────────────────────┐
│      PyInstaller Build Pipeline         │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐                      │
│  │ Python Code  │                      │
│  │ + Frontend   │                      │
│  │ + Assets     │                      │
│  └──────┬───────┘                      │
│         │                               │
│         ▼                               │
│  ┌──────────────┐                      │
│  │  Analysis    │  Find dependencies   │
│  │  Phase       │  Collect imports     │
│  └──────┬───────┘                      │
│         │                               │
│         ▼                               │
│  ┌──────────────┐                      │
│  │  Build       │  Create executable   │
│  │  Phase       │  Bundle resources    │
│  └──────┬───────┘                      │
│         │                               │
│         ▼                               │
│  ┌──────────────┐                      │
│  │ Standalone   │  Windows: .exe       │
│  │ Executable   │  macOS: .app         │
│  │              │  Linux: binary       │
│  └──────────────┘                      │
└─────────────────────────────────────────┘
```

### Tauri Build Process

```
┌─────────────────────────────────────────┐
│         Tauri Build Pipeline            │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │  Frontend    │  │   Backend    │   │
│  │  (React)     │  │  (Python)    │   │
│  └──────┬───────┘  └──────┬───────┘   │
│         │                  │            │
│         ▼                  ▼            │
│  ┌──────────────┐  ┌──────────────┐   │
│  │  WebView     │◄─┤ Rust Core    │   │
│  │  Bundle      │  │ + Python     │   │
│  └──────┬───────┘  └──────┬───────┘   │
│         │                  │            │
│         └────────┬─────────┘            │
│                  ▼                      │
│         ┌──────────────┐               │
│         │ Native App   │ 10-30MB!     │
│         │ (.app/.exe)  │               │
│         └──────────────┘               │
└─────────────────────────────────────────┘
```

## File Size Benchmarks

### Windows
| Method | Size | Notes |
|--------|------|-------|
| PyInstaller (one-file) | 120 MB | Includes Python runtime |
| PyInstaller (one-dir) | 180 MB | Faster startup |
| PyInstaller + UPX | 90 MB | Compressed |
| Electron | 140 MB | Includes Chromium |
| Tauri | 25 MB | Uses OS WebView |

### macOS
| Method | Size | Notes |
|--------|------|-------|
| PyInstaller .app | 200 MB | Includes dependencies |
| Electron .app | 150 MB | DMG ~100MB |
| Tauri .app | 30 MB | DMG ~20MB |

### Linux
| Method | Size | Notes |
|--------|------|-------|
| PyInstaller binary | 160 MB | Self-contained |
| AppImage | 180 MB | Portable |
| Flatpak | 100 MB | Shared runtime |
| Snap | 120 MB | Compressed |

## Code Signing

### macOS
```bash
# Sign with Developer ID
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Your Name (TEAMID)" \
  --options runtime \
  dist/PokerTool.app

# Verify signature
codesign -vvv --deep --strict dist/PokerTool.app
spctl -a -vvv -t install dist/PokerTool.app

# Notarize
xcrun notarytool submit PokerTool.dmg \
  --apple-id "email@example.com" \
  --team-id "TEAMID" \
  --password "app-specific-password" \
  --wait

# Staple ticket
xcrun stapler staple dist/PokerTool.app
```

### Windows
```bash
# Sign with Authenticode certificate
signtool sign /f certificate.pfx \
  /p password \
  /t http://timestamp.digicert.com \
  /fd SHA256 \
  /d "PokerTool" \
  dist/PokerTool.exe

# Verify signature
signtool verify /pa dist/PokerTool.exe
```

### Linux
```bash
# Sign AppImage
gpg --armor --detach-sign PokerTool-x86_64.AppImage

# Verify
gpg --verify PokerTool-x86_64.AppImage.asc
```

## Auto-Update Implementation

### PyInstaller + Custom Updater
```python
# src/pokertool/updater.py
import requests
from packaging import version

def check_for_updates():
    response = requests.get(
        "https://api.github.com/repos/gmanldn/pokertool/releases/latest"
    )
    latest_version = response.json()["tag_name"]
    
    if version.parse(latest_version) > version.parse(CURRENT_VERSION):
        return {
            "available": True,
            "version": latest_version,
            "download_url": get_platform_download_url(response.json())
        }
    return {"available": False}
```

### Tauri Auto-Update
```rust
// Built-in updater
use tauri::updater::builder;

builder()
    .endpoints(vec!["https://api.pokertool.io/updates"])
    .build()?
    .check_update()
    .await?;
```

### Electron Auto-Update
```typescript
// electron-builder auto-updater
import { autoUpdater } from 'electron-updater';

autoUpdater.checkForUpdatesAndNotify();
```

## Testing Checklist

Before release, test on clean systems:

### Windows
- [ ] Install on Windows 10 (no Python)
- [ ] Install on Windows 11 (no Python)
- [ ] Test with Windows Defender enabled
- [ ] Verify file associations
- [ ] Test uninstaller
- [ ] Check Start Menu shortcuts
- [ ] Verify auto-update

### macOS
- [ ] Install on macOS 12 Monterey
- [ ] Install on macOS 13 Ventura
- [ ] Install on macOS 14 Sonoma
- [ ] Test on both Intel and Apple Silicon
- [ ] Verify Gatekeeper acceptance
- [ ] Test drag-to-Applications
- [ ] Check Dock icon
- [ ] Verify auto-update

### Linux
- [ ] Test on Ubuntu 22.04 LTS
- [ ] Test on Fedora 38
- [ ] Test on Arch Linux
- [ ] Test AppImage on multiple distros
- [ ] Verify Flatpak sandboxing
- [ ] Test Snap confinement
- [ ] Check desktop integration
- [ ] Verify auto-update

## Distribution Strategies

### Free & Open Source
1. GitHub Releases for direct download
2. Flathub for Linux
3. Snapcraft Store for Linux
4. Homebrew for macOS
5. Winget for Windows

### Commercial
1. Mac App Store ($99/year)
2. Microsoft Store ($19 one-time)
3. Direct website downloads
4. License key system
5. Subscription model with updates

### Hybrid
1. Free version on package managers
2. Pro version on app stores
3. Direct downloads for all
4. In-app purchases for features

## CI/CD Integration

### GitHub Actions - Multi-Platform Build

```yaml
name: Build Desktop Apps

on:
  release:
    types: [created]

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
    
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
        run: pyinstaller packaging/pyinstaller/pokertool_gui.spec
      
      - name: Create DMG (macOS)
        if: matrix.os == 'macos-latest'
        run: |
          hdiutil create -volname "PokerTool" \
            -srcfolder dist/PokerTool.app \
            -ov -format UDZO \
            dist/PokerTool-${{ github.ref_name }}-macOS.dmg
      
      - name: Create Installer (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          makensis packaging/nsis/pokertool-installer.nsi
      
      - name: Create AppImage (Linux)
        if: matrix.os == 'ubuntu-latest'
        run: |
          appimagetool dist/PokerTool dist/PokerTool-x86_64.AppImage
      
      - name: Upload to Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/PokerTool-*
```

## Troubleshooting

### Common Issues

**Antivirus False Positives (Windows)**
- Sign your executable with code signing certificate
- Submit to Microsoft for analysis
- Use reputable installer framework (NSIS, Inno Setup)

**Gatekeeper Issues (macOS)**
- Sign with Developer ID certificate
- Notarize the app through Apple
- Staple the notarization ticket

**Missing Dependencies**
- Use PyInstaller hooks to include hidden imports
- Bundle system libraries explicitly
- Test on clean VM/machine

**Large File Size**
- Exclude unnecessary modules
- Use UPX compression
- Consider one-file vs one-dir trade-offs
- For smallest size, use Tauri instead

## Best Practices

1. ✅ Always test on clean systems without development tools
2. ✅ Sign your code for all platforms
3. ✅ Implement automatic updates
4. ✅ Provide uninstallers
5. ✅ Create proper installers, not just zips
6. ✅ Include version info in executables
7. ✅ Set up crash reporting
8. ✅ Provide rollback mechanism
9. ✅ Document system requirements
10. ✅ Test on minimum supported OS versions

## Getting Help

- **Issues:** [GitHub Issues](https://github.com/gmanldn/pokertool/issues)
- **Packaging Questions:** Label as `packaging`
- **Platform-Specific:** Use `windows`, `macos`, or `linux` labels

## Contributing

Contributions welcome! See [CONTRIBUTING.md](../../CONTRIBUTING.md) for:
- Adding new packaging methods
- Improving documentation
- Testing on different platforms
- Submitting bug reports

## Resources

### PyInstaller
- [PyInstaller Manual](https://pyinstaller.org/)
- [Hooks Repository](https://github.com/pyinstaller/pyinstaller-hooks-contrib)

### Tauri
- [Tauri Documentation](https://tauri.app/)
- [Tauri Bundling](https://tauri.app/v1/guides/building/)

### Electron
- [Electron Forge](https://www.electronforge.io/)
- [electron-builder](https://www.electron.build/)

### Code Signing
- [Apple Developer](https://developer.apple.com/support/code-signing/)
- [Microsoft Authenticode](https://docs.microsoft.com/en-us/windows-hardware/drivers/install/authenticode)

## License

All documentation and packaging scripts in this directory are released under the Apache License 2.0.

---

**Last Updated:** October 2025  
**Maintainer:** PokerTool Team  
**Version:** 1.0.0
