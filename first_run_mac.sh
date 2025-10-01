#!/bin/bash
# first_run_mac.sh - Launcher script for macOS to ensure Python is installed and run start.py

echo "Checking for Python installation..."

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Installing Python using Homebrew..."
    brew install python3
else
    echo "Python3 is already installed."
fi

# Run start.py with Python3
echo "Running start.py..."
python3 start.py

exit 0
