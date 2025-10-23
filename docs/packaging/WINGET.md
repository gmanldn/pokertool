# Windows Package Manager (winget) Guide

## Overview

This guide covers submitting PokerTool to the Windows Package Manager (winget), enabling easy installation on Windows 11 and Windows 10 via the `winget install` command.

## What is winget?

Windows Package Manager (winget) is Microsoft's official package manager for Windows, providing:
- Command-line package installation
- Automatic updates
- Package discovery
- Manifest-based configuration
- Integration with Windows 11

## Prerequisites

- GitHub account
- Windows installer (MSI or EXE)
- Hosted release artifacts
- winget CLI installed for testing

## Installation

```powershell
# winget is pre-installed on Windows 11
# For Windows 10, install from Microsoft Store
# Or download from GitHub
winget --version
```

## Manifest Structure

### Manifest Files

Winget uses YAML manifests split into multiple files:

```
manifests/
└── g/
    └── gmanldn/
        └── PokerTool/
            ├── 1.0.0.yaml          # Version manifest
            ├── 1.0.0.installer.yaml # Installer manifest
            └── 1.0.0.locale.en-US.yaml  # Locale manifest
```

### Version Manifest

`manifests/g/gmanldn/PokerTool/1.0.0.yaml`:

```yaml
# yaml-language-server: $schema=https://aka.ms/winget-manifest.version.1.5.0.schema.json

PackageIdentifier: gmanldn.PokerTool
PackageVersion: 1.0.0
DefaultLocale: en-US
ManifestType: version
ManifestVersion: 1.5.0
```

### Installer Manifest

`manifests/g/gmanldn/PokerTool/1.0.0.installer.yaml`:

```yaml
# yaml-language-server: $schema=https://aka.ms/winget-manifest.installer.1.5.0.schema.json

PackageIdentifier: gmanldn.PokerTool
PackageVersion: 1.0.0
Platform:
  - Windows.Desktop
MinimumOSVersion: 10.0.0.0
InstallerType: msi
Scope: user
InstallModes:
  - interactive
  - silent
  - silentWithProgress
UpgradeBehavior: install
ReleaseDate: 2025-01-15
Installers:
  - Architecture: x64
    InstallerUrl: https://github.com/gmanldn/pokertool/releases/download/v1.0.0/PokerTool-1.0.0-win64.msi
    InstallerSha256: 1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF
    ProductCode: '{12345678-1234-1234-1234-123456789012}'
  - Architecture: x86
    InstallerUrl: https://github.com/gmanldn/pokertool/releases/download/v1.0.0/PokerTool-1.0.0-win32.msi
    InstallerSha256: ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890
    ProductCode: '{87654321-4321-4321-4321-210987654321}'
ManifestType: installer
ManifestVersion: 1.5.0
```

### Locale Manifest

`manifests/g/gmanldn/PokerTool/1.0.0.locale.en-US.yaml`:

```yaml
# yaml-language-server: $schema=https://aka.ms/winget-manifest.defaultLocale.1.5.0.schema.json

PackageIdentifier: gmanldn.PokerTool
PackageVersion: 1.0.0
PackageLocale: en-US
Publisher: PokerTool Team
PublisherUrl: https://github.com/gmanldn/pokertool
PublisherSupportUrl: https://github.com/gmanldn/pokertool/issues
# PrivacyUrl: 
Author: PokerTool Team
PackageName: PokerTool
PackageUrl: https://github.com/gmanldn/pokertool
License: MIT
LicenseUrl: https://github.com/gmanldn/pokertool/blob/main/LICENSE
# Copyright: 
# CopyrightUrl: 
ShortDescription: AI-Powered Poker Analysis Tool
Description: |-
  PokerTool is a comprehensive poker analysis and decision support tool
  powered by artificial intelligence. It provides real-time hand analysis,
  range calculations, and strategic advice to improve your poker game.
  
  Features:
  - Real-time hand analysis
  - Range calculations
  - Strategic recommendations
  - Session tracking
  - Hand history analysis
  - Learning system
Moniker: pokertool
Tags:
  - poker
  - analysis
  - ai
  - machine-learning
  - card-game
  - poker-tool
  - gambling
  - strategy
# Agreements: 
ReleaseNotes: |-
  - Initial release
  - Core poker analysis features
  - Real-time decision support
  - Session tracking
ReleaseNotesUrl: https://github.com/gmanldn/pokertool/releases/tag/v1.0.0
# PurchaseUrl: 
# InstallationNotes: 
Documentations:
  - DocumentLabel: User Guide
    DocumentUrl: https://github.com/gmanldn/pokertool/blob/main/docs/MANUAL.md
  - DocumentLabel: Quick Start
    DocumentUrl: https://github.com/gmanldn/pokertool/blob/main/docs/QUICKSTART.md
ManifestType: defaultLocale
ManifestVersion: 1.5.0
```

## Creating Manifests

### Using wingetcreate

```powershell
# Install wingetcreate
winget install Microsoft.WingetCreate

# Create new package manifest
wingetcreate new https://github.com/gmanldn/pokertool/releases/download/v1.0.0/PokerTool-1.0.0-win64.msi

# Update existing package
wingetcreate update gmanldn.PokerTool -v 1.1.0 -u https://github.com/gmanldn/pokertool/releases/download/v1.1.0/PokerTool-1.1.0-win64.msi

# Submit to winget-pkgs
wingetcreate submit ./manifests/g/gmanldn/PokerTool/1.0.0/
```

### Manual Creation

```powershell
# Create directory structure
mkdir -p manifests/g/gmanldn/PokerTool/1.0.0

# Create manifests (see templates above)
# Edit manifests/g/gmanldn/PokerTool/1.0.0/*.yaml

# Calculate SHA256
Get-FileHash PokerTool-1.0.0-win64.msi -Algorithm SHA256

# Get MSI Product Code
$msi = New-Object -ComObject WindowsInstaller.Installer
$db = $msi.GetType().InvokeMember("OpenDatabase", "InvokeMethod", $null, $msi, @("PokerTool-1.0.0-win64.msi", 0))
$view = $db.GetType().InvokeMember("OpenView", "InvokeMethod", $null, $db, ("SELECT Value FROM Property WHERE Property='ProductCode'"))
$view.GetType().InvokeMember("Execute", "InvokeMethod", $null, $view, $null)
$record = $view.GetType().InvokeMember("Fetch", "InvokeMethod", $null, $view, $null)
$productCode = $record.GetType().InvokeMember("StringData", "GetProperty", $null, $record, 1)
Write-Host $productCode
```

## Submission Process

### 1. Fork winget-pkgs Repository

```bash
# Fork on GitHub
gh repo fork microsoft/winget-pkgs --clone

# Or manually
git clone https://github.com/YOUR_USERNAME/winget-pkgs.git
cd winget-pkgs
```

### 2. Create Branch

```bash
git checkout -b gmanldn.PokerTool-1.0.0
```

### 3. Add Manifests

```bash
# Create directory structure
mkdir -p manifests/g/gmanldn/PokerTool/1.0.0

# Copy your manifest files
cp path/to/your/manifests/* manifests/g/gmanldn/PokerTool/1.0.0/

# Validate manifests
winget validate --manifest manifests/g/gmanldn/PokerTool/1.0.0/
```

### 4. Test Installation

```powershell
# Test local manifest
winget install --manifest manifests/g/gmanldn/PokerTool/1.0.0/

# Verify installation
winget list gmanldn.PokerTool

# Test uninstall
winget uninstall gmanldn.PokerTool
```

### 5. Commit and Push

```bash
# Stage files
git add manifests/g/gmanldn/PokerTool/

# Commit
git commit -m "New package: gmanldn.PokerTool version 1.0.0"

# Push
git push origin gmanldn.PokerTool-1.0.0
```

### 6. Create Pull Request

```bash
# Create PR via GitHub CLI
gh pr create \
  --title "New package: gmanldn.PokerTool version 1.0.0" \
  --body "Add PokerTool - AI-Powered Poker Analysis Tool"

# Or create PR on GitHub web interface
```

## Installer Requirements

### MSI Installer

Recommended for winget. Must include:
- Product Code (GUID)
- Product Version
- Manufacturer
- Silent install support
- Uninstall support

### EXE Installer

Supported but MSI preferred. Requirements:
- Silent install flags documented
- Uninstall registry entry
- Return codes

### Installer Types

```yaml
# MSI
InstallerType: msi

# Nullsoft (NSIS)
InstallerType: nullsoft

# Inno Setup
InstallerType: inno

# WiX
InstallerType: wix

# Burn (WiX toolset)
InstallerType: burn

# Generic EXE
InstallerType: exe
```

## Silent Installation

### MSI Silent Install

```powershell
# Standard MSI silent install
msiexec /i PokerTool.msi /qn /norestart

# With log
msiexec /i PokerTool.msi /qn /l*v install.log
```

### NSIS Silent Install

```powershell
# NSIS silent install
PokerTool-Setup.exe /S

# With custom install directory
PokerTool-Setup.exe /S /D=C:\CustomPath
```

## Update Mechanism

### Version Updates

```yaml
# manifests/g/gmanldn/PokerTool/1.1.0.installer.yaml
PackageVersion: 1.1.0  # Updated version
ReleaseDate: 2025-02-15  # Updated date
Installers:
  - Architecture: x64
    InstallerUrl: https://github.com/gmanldn/pokertool/releases/download/v1.1.0/PokerTool-1.1.0-win64.msi  # Updated URL
    InstallerSha256: NEW_SHA256_HERE  # Updated hash
```

### Upgrade Behavior

```yaml
UpgradeBehavior: install  # Default: install over old version
# or
UpgradeBehavior: uninstallPrevious  # Uninstall then install
```

## Advanced Features

### Multiple Installers

```yaml
Installers:
  # 64-bit MSI
  - Architecture: x64
    InstallerType: msi
    InstallerUrl: https://example.com/PokerTool-x64.msi
    InstallerSha256: SHA256_HERE
  
  # 32-bit MSI
  - Architecture: x86
    InstallerType: msi
    InstallerUrl: https://example.com/PokerTool-x86.msi
    InstallerSha256: SHA256_HERE
  
  # ARM64
  - Architecture: arm64
    InstallerType: msi
    InstallerUrl: https://example.com/PokerTool-arm64.msi
    InstallerSha256: SHA256_HERE
```

### Installer Switches

```yaml
InstallerSwitches:
  Silent: /quiet /norestart
  SilentWithProgress: /passive /norestart
  Interactive: /interactive
  InstallLocation: INSTALLDIR="<INSTALLPATH>"
  Log: /log "<LOGPATH>"
  Upgrade: REINSTALL=ALL REINSTALLMODE=vomus
  Custom: /CUSTOMSWITCH
```

### Dependencies

```yaml
Dependencies:
  WindowsFeatures:
    - IIS-WebServer
  WindowsLibraries:
    - Microsoft.VCLibs.140.00
  PackageDependencies:
    - PackageIdentifier: Microsoft.DotNet.Runtime.8
      MinimumVersion: 8.0.0
  ExternalDependencies:
    - Python 3.12
    - PostgreSQL
```

### File Extensions

```yaml
FileExtensions:
  - .pht
  - .pkr
  - .poker
```

### Protocols

```yaml
Protocols:
  - pokertool
```

### Commands

```yaml
Commands:
  - pokertool
  - pt
```

## Testing

### Local Testing

```powershell
# Test manifest validation
winget validate --manifest path/to/manifests

# Test install from local manifest
winget install --manifest path/to/manifests

# Test with different parameters
winget install --manifest path/to/manifests --silent
winget install --manifest path/to/manifests --location "C:\CustomPath"

# Test upgrade
winget upgrade gmanldn.PokerTool

# Test uninstall
winget uninstall gmanldn.PokerTool
```

### Automated Testing

```powershell
# Test script
$manifest = "manifests/g/gmanldn/PokerTool/1.0.0"

# Validate
winget validate --manifest $manifest
if ($LASTEXITCODE -ne 0) { exit 1 }

# Install
winget install --manifest $manifest --silent
if ($LASTEXITCODE -ne 0) { exit 1 }

# Verify
$installed = winget list --id gmanldn.PokerTool
if ($installed -notmatch "PokerTool") { exit 1 }

# Uninstall
winget uninstall gmanldn.PokerTool --silent
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "All tests passed!"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Winget Submission

on:
  release:
    types: [published]

jobs:
  publish-winget:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install wingetcreate
        run: |
          Invoke-WebRequest https://aka.ms/wingetcreate/latest -OutFile wingetcreate.exe
          
      - name: Create/Update manifest
        run: |
          if (Test-Path "manifests/g/gmanldn/PokerTool") {
            ./wingetcreate.exe update gmanldn.PokerTool \
              --version ${{ github.event.release.tag_name }} \
              --urls "${{ github.event.release.assets[0].browser_download_url }}" \
              --token ${{ secrets.WINGET_TOKEN }}
          } else {
            ./wingetcreate.exe new \
              "${{ github.event.release.assets[0].browser_download_url }}" \
              --token ${{ secrets.WINGET_TOKEN }}
          }
      
      - name: Submit to winget-pkgs
        run: |
          ./wingetcreate.exe submit \
            ./manifests/g/gmanldn/PokerTool/${{ github.event.release.tag_name }} \
            --token ${{ secrets.WINGET_TOKEN }}
```

## Best Practices

1. **Use MSI installers** - Preferred by winget
2. **Provide silent install** - Required for automation
3. **Include all architectures** - x64, x86, ARM64 if applicable
4. **Test thoroughly** - Test install, upgrade, uninstall
5. **Update promptly** - Keep package current with releases
6. **Good metadata** - Complete descriptions and tags
7. **Follow naming** - Use consistent PackageIdentifier
8. **Validate manifests** - Always validate before submitting

## Troubleshooting

### Validation Errors

```powershell
# Common issues and fixes

# Invalid SHA256
Get-FileHash installer.msi -Algorithm SHA256

# Missing required fields
# Check schema: https://aka.ms/winget-manifest.installer.1.5.0.schema.json

# Invalid YAML syntax
# Use YAML validator or VS Code extension
```

### Installation Failures

```powershell
# Check installer logs
Get-Content "$env:LOCALAPPDATA\Packages\Microsoft.DesktopAppInstaller_8wekyb3d8bbwe\LocalState\DiagOutputDir\*.log"

# Test installer directly
msiexec /i PokerTool.msi /l*v install.log
Get-Content install.log
```

## Next Steps

- Review [Chocolatey Package](CHOCOLATEY.md)
- Explore [Native Installers](NATIVE_INSTALLERS.md)
- Set up [Auto-Updater](../features/AUTO_UPDATER.md)

## References

- [winget Documentation](https://docs.microsoft.com/en-us/windows/package-manager/)
- [Manifest Schema](https://github.com/microsoft/winget-pkgs/tree/master/doc/manifest/schema)
- [Contributing Guide](https://github.com/microsoft/winget-pkgs/blob/master/CONTRIBUTING.md)
- [wingetcreate](https://github.com/microsoft/winget-create)
- [Best Practices](https://github.com/microsoft/winget-pkgs/blob/master/AUTHORING_MANIFESTS.md)
