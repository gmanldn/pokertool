#!/bin/bash
# first_run_linux.sh - Launcher script for Linux to ensure Python is installed and run start.py

echo "Checking for Python installation..."

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Installing Python using apt..."
    sudo apt update
    sudo apt install python3 -y
else
    echo "Python3 is already installed."
fi

# Run start.py with Python3
echo "Running start.py..."
python3 start.py

exit 0
