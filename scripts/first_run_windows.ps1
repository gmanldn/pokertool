# first_run_windows.ps1 - Complete bootstrap script for Windows
# This script ensures Python 3.8+ is installed and sets up PokerTool from scratch

# Requires PowerShell 5.0 or higher

#Requires -Version 5.0

# Enable strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=================================="
Write-Host "PokerTool - Windows Bootstrap"
Write-Host "=================================="
Write-Host ""

# Change to project root directory (parent of scripts/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Logging functions
function Log-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Log-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Log-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Check if running as Administrator
function Test-Administrator {
    $currentUser = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check Windows version
Log-Info "Checking Windows version..."
$WindowsVersion = [System.Environment]::OSVersion.Version
Log-Info "Windows version: $($WindowsVersion.Major).$($WindowsVersion.Minor)"

if ($WindowsVersion.Major -lt 10) {
    Log-Warn "Windows 10 or higher is recommended"
}

# Check for Python 3
Log-Info "Checking for Python 3..."
$PythonCmd = $null
$PythonVersion = $null

# Try to find Python 3
$pythonPaths = @("python", "python3", "py")
foreach ($pyCmd in $pythonPaths) {
    try {
        $version = & $pyCmd --version 2>&1
        if ($version -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            
            if ($major -ge 3 -and $minor -ge 8) {
                $PythonCmd = $pyCmd
                $PythonVersion = $version
                Log-Info "Found Python: $PythonVersion"
                break
            } else {
                Log-Warn "$pyCmd version $version is too old (need 3.8+)"
            }
        }
    } catch {
        # Command not found, continue
    }
}

# Install Python if not found or too old
if (-not $PythonCmd) {
    Log-Warn "Python 3.8+ not found. Installing Python..."
    
    # Check if winget is available (Windows 10 1809+ / Windows 11)
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Log-Info "Installing Python via winget..."
        try {
            winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
            Log-Info "✓ Python installed via winget"
        } catch {
            Log-Warn "winget installation failed, falling back to manual installer"
            $useManualInstall = $true
        }
    } else {
        $useManualInstall = $true
    }
    
    # Manual installation fallback
    if ($useManualInstall) {
        Log-Info "Downloading Python installer..."
        $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        $installerPath = "$env:TEMP\python-installer.exe"
        
        try {
            # Download with progress
            $ProgressPreference = 'SilentlyContinue'
            Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
            Log-Info "Downloaded Python installer"
            
            # Install Python
            Log-Info "Installing Python (this may take a few minutes)..."
            $installArgs = "/quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1"
            Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -NoNewWindow
            
            # Clean up
            Remove-Item $installerPath -Force
            Log-Info "✓ Python installed"
            
        } catch {
            Log-Error "Failed to install Python: $_"
            Log-Error "Please install Python 3.8+ manually from https://www.python.org"
            exit 1
        }
    }
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Try to find Python again
    $PythonCmd = $null
    foreach ($pyCmd in $pythonPaths) {
        try {
            $version = & $pyCmd --version 2>&1
            if ($version -match "Python 3") {
                $PythonCmd = $pyCmd
                $PythonVersion = $version
                break
            }
        } catch {}
    }
    
    if (-not $PythonCmd) {
        Log-Error "Python installation completed but cannot find python command"
        Log-Error "You may need to restart your terminal or computer"
        Log-Info "After restart, run: python start.py"
        exit 1
    }
} else {
    Log-Info "✓ Python 3.8+ already installed"
}

Log-Info "Using: $PythonVersion"

# Check for pip
Log-Info "Checking for pip..."
try {
    & $PythonCmd -m pip --version | Out-Null
    Log-Info "✓ pip already installed"
} catch {
    Log-Warn "pip not found. Installing pip..."
    & $PythonCmd -m ensurepip --upgrade
    Log-Info "✓ pip installed"
}

# Upgrade pip to latest version
Log-Info "Upgrading pip..."
try {
    & $PythonCmd -m pip install --upgrade pip --quiet
    Log-Info "✓ pip upgraded"
} catch {
    Log-Warn "Failed to upgrade pip (non-critical)"
}

# Check for Visual C++ Build Tools (needed for some Python packages)
Log-Info "Checking for Visual C++ Build Tools..."
$vcInstalled = $false

# Check registry for Visual Studio or Build Tools
$vsKeys = @(
    "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0",
    "HKLM:\SOFTWARE\Microsoft\VisualStudio\15.0",
    "HKLM:\SOFTWARE\Microsoft\VisualStudio\16.0",
    "HKLM:\SOFTWARE\Microsoft\VisualStudio\17.0"
)

foreach ($key in $vsKeys) {
    if (Test-Path $key) {
        $vcInstalled = $true
        break
    }
}

if (-not $vcInstalled) {
    Log-Warn "Visual C++ Build Tools not detected"
    Log-Warn "Some Python packages may fail to install"
    Log-Info "You can install them from: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
} else {
    Log-Info "✓ Visual C++ Build Tools detected"
}

# Optional: Check for Node.js
Log-Info "Checking for Node.js..."
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Log-Info "✓ Node.js already installed: $nodeVersion"
} else {
    Log-Warn "Node.js not found (optional, for frontend features)"
    Log-Info "Install from: https://nodejs.org/"
}

# Optional: Check for Tesseract OCR
Log-Info "Checking for Tesseract OCR..."
if (Get-Command tesseract -ErrorAction SilentlyContinue) {
    $tesseractVersion = tesseract --version 2>&1 | Select-Object -First 1
    Log-Info "✓ Tesseract already installed"
} else {
    Log-Warn "Tesseract OCR not found (required for screen scraping)"
    Log-Info "Install from: https://github.com/UB-Mannheim/tesseract/wiki"
    Log-Info "Or use: winget install UB-Mannheim.TesseractOCR"
}

Write-Host ""
Write-Host "=================================="
Log-Info "Bootstrap complete! Launching PokerTool..."
Write-Host "=================================="
Write-Host ""

# Run start.py
$exitCode = 0
try {
    & $PythonCmd start.py $args
    $exitCode = $LASTEXITCODE
} catch {
    Log-Error "Failed to run start.py: $_"
    $exitCode = 1
}

exit $exitCode
