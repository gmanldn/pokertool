# first_run_windows.ps1 - Launcher script for Windows to ensure Python is installed and run start.py

Write-Host "Checking for Python installation..."

# Check if Python is installed by checking for python.exe
$pythonPath = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonPath) {
    Write-Host "Python not found. Downloading and installing the latest Python..."

    # Download the latest Python installer for Windows
    $pythonUrl = "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe"
    $installerPath = "$env:TEMP\python-installer.exe"

    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath
        Write-Host "Downloaded Python installer."

        # Install Python silently, adding to PATH
        $args = "/quiet InstallAllUsers=1 PrependPath=1"
        Start-Process -FilePath $installerPath -ArgumentList $args -Wait -NoNewWindow
        Write-Host "Python installed successfully."

        # Clean up installer
        Remove-Item $installerPath -Force
    } catch {
        Write-Error "Failed to install Python: $_"
        exit 1
    }
} else {
    Write-Host "Python is already installed at: $($pythonPath.Source)"
}

# Refresh environment variables
$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Run start.py with Python
Write-Host "Running start.py..."
& python start.py

exit 0
