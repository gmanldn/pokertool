#!/bin/bash
# PokerTool Quick Start Script with Full Tab Support

# Kill any existing processes
pkill -9 -f "python.*scripts/start.py" 2>/dev/null
pkill -9 -f "python.*cli.py" 2>/dev/null
pkill -9 -f "paddlepaddle" 2>/dev/null
sleep 2

# Set up environment
cd /Users/georgeridout/Documents/github/pokertool

# Find venv site-packages dynamically
VENV_SITE_PACKAGES=$(find .venv/lib -name "site-packages" -type d | head -1)

if [ -z "$VENV_SITE_PACKAGES" ]; then
    echo "❌ Could not find venv site-packages"
    exit 1
fi

echo "✅ Found venv packages: $VENV_SITE_PACKAGES"

# Set clean PYTHONPATH with venv packages FIRST
export PYTHONPATH="${VENV_SITE_PACKAGES}:${PWD}/src"
export TK_SILENCE_DEPRECATION=1

echo "✅ PYTHONPATH configured"
echo "🚀 Launching PokerTool GUI with all 8 tabs..."

# Use system Python for tkinter support with venv packages accessible
/usr/bin/python3 src/pokertool/cli.py gui 2>&1 | tee /tmp/pokertool_full.log
