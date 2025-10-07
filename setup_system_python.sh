#!/bin/bash
# Setup PokerTool with system Python (no venv)
# This avoids tkinter/venv compatibility issues

set -e

echo "🔧 Setting up PokerTool with system Python..."
echo "This will install all dependencies to your system Python installation."
echo ""

# Find system Python
PYTHON_CMD=""
for cmd in python3 /usr/bin/python3 /usr/local/bin/python3; do
    if command -v "$cmd" &> /dev/null; then
        PYTHON_CMD="$cmd"
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ No system Python 3 found"
    exit 1
fi

echo "✅ Using: $PYTHON_CMD"
$PYTHON_CMD --version
echo ""

# Check if tkinter is available
echo "🔍 Checking for tkinter..."
if $PYTHON_CMD -c "import tkinter" 2>/dev/null; then
    echo "✅ tkinter available"
else
    echo "❌ tkinter not available"
    echo "Install with: brew install python-tk"
    exit 1
fi
echo ""

# Install critical dependencies to system Python
echo "📦 Installing critical dependencies to system Python..."
$PYTHON_CMD -m pip install --user \
    'numpy<2.0' \
    'opencv-python>=4.8.0,<4.10.0' \
    'Pillow>=10.0.0' \
    'pytesseract>=0.3.10' \
    'mss>=9.0.0' \
    'requests>=2.32.0' \
    'pyobjc-framework-Quartz>=9.0'

echo ""
echo "✅ Setup complete!"
echo ""
echo "To launch PokerTool:"
echo "  $PYTHON_CMD src/pokertool/cli.py gui"
echo ""
