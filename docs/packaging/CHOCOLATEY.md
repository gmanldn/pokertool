# Chocolatey Package Guide

## Overview

This guide covers creating a Chocolatey package for PokerTool, enabling easy installation on Windows via the `choco install` command.

## What is Chocolatey?

Chocolatey is a popular package manager for Windows that provides:
- Command-line package management
- Automatic dependency resolution
- Silent installations
- Version management
- Community package repository

## Prerequisites

- Chocolatey installed
- Windows installer (MSI, EXE, or ZIP)
- NuGet package structure knowledge
- Chocolatey account (for publishing)

## Installation

```powershell
# Install Chocolatey (run as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Verify installation
choco --version
```

## Package Structure

```
pokertool/
├── pokertool.nuspec              # Package metadata
├── tools/
│   ├── chocolateyinstall.ps1    # Install script
│   ├── chocolateyuninstall.ps1  # Uninstall script
│   └── VERIFICATION.txt         # Checksum verification
├── legal/
│   ├── LICENSE.txt
│   └── VERIFICATION.txt
└── icon.png                      # Package icon
```

## Creating the Package

### 1. Initialize Package

```powershell
# Create package directory
mkdir pokertool
cd pokertool

# Create nuspec file
choco new pokertool

# Or manually create structure
mkdir tools, legal
```

### 2. Package Metadata (nuspec)

Create `pokertool.nuspec`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>pokertool</id>
    <version>1.0.0</version>
    <packageSourceUrl>https://github.com/gmanldn/pokertool</packageSourceUrl>
    <owners>gmanldn</owners>
    
    <title>PokerTool</title>
    <authors>PokerTool Team</authors>
    <projectUrl>https://github.com/gmanldn/pokertool</projectUrl>
    <iconUrl>https://raw.githubusercontent.com/gmanldn/pokertool/main/assets/pokertool-icon.png</iconUrl>
    
    <copyright>2025 PokerTool Team</copyright>
    <licenseUrl>https://github.com/gmanldn/pokertool/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <projectSourceUrl>https://github.com/gmanldn/pokertool</projectSourceUrl>
    <docsUrl>https://github.com/gmanldn/pokertool/blob/main/docs/MANUAL.md</docsUrl>
    <bugTrackerUrl>https://github.com/gmanldn/pokertool/issues</bugTrackerUrl>
    
    <tags>poker analysis ai machine-learning strategy card-game</tags>
    <summary>AI-Powered Poker Analysis Tool</summary>
    <description>
PokerTool is a comprehensive poker analysis and decision support tool powered by artificial intelligence.

## Features
- Real-time hand analysis
- Range calculations
- Strategic recommendations
- Session tracking
- Hand history analysis
- Learning system

## Requirements
- Windows 10 or later
- 4GB RAM minimum
- .NET Framework 4.8 or later
    </description>
    
    <releaseNotes>https://github.com/gmanldn/pokertool/releases/tag/v1.0.0</releaseNotes>
    
    <dependencies>
      <dependency id="dotnet-runtime" version="8.0.0" />
      <dependency id="python" version="3.12.0" />
    </dependencies>
  </metadata>
  
  <files>
    <file src="tools\**" target="tools" />
    <file src="legal\**" target="legal" />
  </files>
</package>
```

### 3. Install Script

Create `tools/chocolateyinstall.ps1`:

```powershell
$ErrorActionPreference = 'Stop'

$packageName = 'pokertool'
$toolsDir = "$(Split-Path -parent $MyInvocation.MyCommand.Definition)"
$url64 = 'https://github.com/gmanldn/pokertool/releases/download/v1.0.0/PokerTool-1.0.0-win64.msi'

$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  fileType      = 'msi'
  url64bit      = $url64
  
  softwareName  = 'PokerTool*'
  
  checksum64    = '1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF'
  checksumType64= 'sha256'
  
  silentArgs    = "/qn /norestart /l*v `"$($env:TEMP)\$($packageName).$($env:chocolateyPackageVersion).MsiInstall.log`""
  validExitCodes= @(0, 3010, 1641)
}

Install-ChocolateyPackage @packageArgs
```

### 4. Uninstall Script

Create `tools/chocolateyuninstall.ps1`:

```powershell
$ErrorActionPreference = 'Stop'

$packageName = 'pokertool'
$softwareName = 'PokerTool*'
$installerType = 'msi'

$silentArgs = '/qn /norestart'
$validExitCodes = @(0, 3010, 1605, 1614, 1641)

[array]$key = Get-UninstallRegistryKey -SoftwareName $softwareName

if ($key.Count -eq 1) {
  $key | % { 
    $file = "$($_.UninstallString)"
    
    if ($installerType -eq 'msi') {
      $silentArgs = "$($_.PSChildName) $silentArgs"
      $file = ''
    }
    
    Uninstall-ChocolateyPackage `
      -PackageName $packageName `
      -FileType $installerType `
      -SilentArgs $silentArgs `
      -ValidExitCodes $validExitCodes `
      -File $file
  }
} elseif ($key.Count -eq 0) {
  Write-Warning "$packageName has already been uninstalled by other means."
} elseif ($key.Count -gt 1) {
  Write-Warning "$($key.Count) matches found!"
  Write-Warning "To prevent accidental data loss, no programs will be uninstalled."
  Write-Warning "Please alert package maintainer the following keys were matched:"
  $key | % {Write-Warning "- $($_.DisplayName)"}
}
```

### 5. Verification File

Create `tools/VERIFICATION.txt`:

```
VERIFICATION
Verification is intended to assist the Chocolatey moderators and community
in verifying that this package's contents are trustworthy.

Package can be verified like this:

1. Download the following:
   
   x64: https://github.com/gmanldn/pokertool/releases/download/v1.0.0/PokerTool-1.0.0-win64.msi

2. You can use one of the following methods to obtain the checksum:
   - Use powershell function 'Get-FileHash'
   - Use Chocolatey utility 'checksum.exe'

   checksum64: 1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF

3. Verify the checksum matches the value in chocolateyInstall.ps1

File 'LICENSE.txt' is obtained from:
   https://github.com/gmanldn/pokertool/blob/main/LICENSE
```

## Building the Package

```powershell
# Pack the package
choco pack

# Result: pokertool.1.0.0.nupkg
```

## Testing Locally

```powershell
# Install from local package
choco install pokertool -source . -y

# Test the installation
pokertool --version

# Uninstall
choco uninstall pokertool -y
```

## Publishing to Community Repository

### 1. Create Chocolatey Account

- Visit https://community.chocolatey.org/
- Create account
- Get API key from account settings

### 2. Set API Key

```powershell
choco apikey --key YOUR_API_KEY_HERE --source https://push.chocolatey.org/
```

### 3. Push Package

```powershell
# Push to Chocolatey Community
choco push pokertool.1.0.0.nupkg --source https://push.chocolatey.org/

# Package will enter moderation queue
# Moderators will review and approve/reject
```

### 4. Package Review Process

- Automated scans run first
- Moderators review manually
- Average wait time: 1-5 days
- Notifications sent via email

## Package Types

### Type 1: Installer Package (Recommended)

```powershell
# Downloads and runs installer
$packageArgs = @{
  packageName   = $packageName
  fileType      = 'msi'
  url64bit      = $url64
  silentArgs    = '/qn /norestart'
  validExitCodes= @(0, 3010, 1641)
  checksum64    = $checksum64
  checksumType64= 'sha256'
}

Install-ChocolateyPackage @packageArgs
```

### Type 2: Portable Package

```powershell
# Extracts and adds to PATH
$packageArgs = @{
  packageName   = $packageName
  unzipLocation = $toolsDir
  url64bit      = $url64
  checksum64    = $checksum64
  checksumType64= 'sha256'
}

Install-ChocolateyZipPackage @packageArgs

# Add to PATH
Install-ChocolateyPath "$toolsDir\bin" 'Machine'
```

### Type 3: Meta Package

```powershell
# Just installs dependencies
# No files in package
```

## Advanced Features

### Auto-Update

Create `update.ps1` for automated updates:

```powershell
import-module au

function global:au_SearchReplace {
    @{
        'tools\chocolateyInstall.ps1' = @{
            "(^[$]url64\s*=\s*)('.*')"      = "`$1'$($Latest.URL64)'"
            "(^[$]checksum64\s*=\s*)('.*')" = "`$1'$($Latest.Checksum64)'"
        }
    }
}

function global:au_GetLatest {
    $releases = 'https://github.com/gmanldn/pokertool/releases/latest'
    $download_page = Invoke-WebRequest -Uri $releases -UseBasicParsing
    
    $re = 'PokerTool-(\d+\.\d+\.\d+)-win64\.msi'
    $url = $download_page.links | ? href -match $re | select -First 1 -expand href
    $version = $matches[1]
    
    @{
        Version = $version
        URL64   = "https://github.com$url"
    }
}

update -ChecksumFor 64
```

### Multiple Versions

```xml
<!-- pokertool.nuspec -->
<version>1.0.0</version>

<!-- pokertool.portable.nuspec -->
<id>pokertool.portable</id>
<version>1.0.0</version>

<!-- pokertool.install.nuspec -->
<id>pokertool.install</id>
<version>1.0.0</version>
```

### Parameters

```powershell
# tools/chocolateyinstall.ps1
$pp = Get-PackageParameters

if ($pp.InstallDir) {
  $installDir = $pp.InstallDir
}

if ($pp.NoDesktopShortcut) {
  $silentArgs += " /NoDesktopShortcut"
}

# Usage:
# choco install pokertool --params="/InstallDir:C:\Custom /NoDesktopShortcut"
```

## Best Practices

1. **Use checksums** - Always include SHA256 checksums
2. **Silent install** - Ensure silent installation works
3. **Proper versioning** - Follow semantic versioning
4. **Good descriptions** - Clear, detailed package description
5. **Include dependencies** - List all required dependencies
6. **Test thoroughly** - Test install/uninstall on clean system
7. **Keep updated** - Update promptly for new releases
8. **Follow guidelines** - Adhere to Chocolatey packaging guidelines

## CI/CD Integration

### GitHub Actions

```yaml
name: Chocolatey Package

on:
  release:
    types: [published]

jobs:
  package:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Chocolatey
        run: |
          Set-ExecutionPolicy Bypass -Scope Process -Force
          iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
      
      - name: Update nuspec version
        run: |
          $version = "${{ github.event.release.tag_name }}".TrimStart('v')
          $nuspec = Get-Content pokertool.nuspec
          $nuspec = $nuspec -replace '<version>.*</version>', "<version>$version</version>"
          Set-Content pokertool.nuspec $nuspec
      
      - name: Update install script
        run: |
          $version = "${{ github.event.release.tag_name }}".TrimStart('v')
          $url = "https://github.com/gmanldn/pokertool/releases/download/${{ github.event.release.tag_name }}/PokerTool-$version-win64.msi"
          
          # Download and get checksum
          Invoke-WebRequest -Uri $url -OutFile installer.msi
          $checksum = (Get-FileHash installer.msi -Algorithm SHA256).Hash
          
          # Update script
          $script = Get-Content tools/chocolateyinstall.ps1
          $script = $script -replace "url64 = '.*'", "url64 = '$url'"
          $script = $script -replace "checksum64 = '.*'", "checksum64 = '$checksum'"
          Set-Content tools/chocolateyinstall.ps1 $script
      
      - name: Pack package
        run: choco pack
      
      - name: Test installation
        run: |
          choco install pokertool -source . -y
          choco uninstall pokertool -y
      
      - name: Push to Chocolatey
        run: |
          choco apikey --key ${{ secrets.CHOCOLATEY_API_KEY }} --source https://push.chocolatey.org/
          choco push pokertool.*.nupkg --source https://push.chocolatey.org/
```

## Troubleshooting

### Common Issues

```powershell
# Invalid checksum
Get-FileHash installer.msi -Algorithm SHA256

# Package won't install
choco install pokertool -y -dv

# Uninstall issues
Get-UninstallRegistryKey -SoftwareName "PokerTool*"

# Path not updated
refreshenv
```

### Validation Errors

```powershell
# Validate package before pushing
choco pack
Test-ChocolateyPackage pokertool.1.0.0.nupkg

# Check for common issues
choco push pokertool.1.0.0.nupkg --source https://push.chocolatey.org/ --debug
```

## Maintenance

### Update Checklist

1. Update version in nuspec
2. Update URLs in install script
3. Calculate new checksums
4. Update VERIFICATION.txt
5. Test locally
6. Pack and push
7. Monitor moderation queue

### Deprecation

```xml
<!-- Mark package as deprecated -->
<metadata>
  <deprecated>true</deprecated>
  <deprecationMessage>This package has been deprecated. Please use 'new-package-id' instead.</deprecationMessage>
</metadata>
```

## Resources

### Helper Functions

```powershell
# Common Chocolatey helpers
Install-ChocolateyPackage
Install-ChocolateyZipPackage
Install-ChocolateyVsixPackage
Install-ChocolateyShortcut
Install-ChocolateyPath
Install-ChocolateyEnvironmentVariable
Get-PackageParameters
Get-UninstallRegistryKey
Update-SessionEnvironment
```

## Next Steps

- Review [Winget Package](WINGET.md)
- Explore [Native Installers](NATIVE_INSTALLERS.md)
- Set up [Auto-Updater](../features/AUTO_UPDATER.md)

## References

- [Chocolatey Documentation](https://docs.chocolatey.org/en-us/)
- [Package Creation](https://docs.chocolatey.org/en-us/create/create-packages)
- [Package Validator](https://docs.chocolatey.org/en-us/community-repository/moderation/package-validator)
- [Helper Reference](https://docs.chocolatey.org/en-us/create/functions/)
- [Best Practices](https://docs.chocolatey.org/en-us/create/create-packages#package-maintainer-best-practices)
