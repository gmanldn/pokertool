#!/bin/bash
# Direct launcher using system Python (bypasses all venv complexity)

cd "$(dirname "$0")"

# Use system Python directly
PYTHON=/usr/bin/python3
PYTHONPATH="$PWD/src"
export PYTHONPATH
export TK_SILENCE_DEPRECATION=1

echo "🚀 Launching PokerTool with system Python..."
echo "   Python: $PYTHON"
echo "   PYTHONPATH: $PYTHONPATH"
echo ""

# Launch GUI
exec $PYTHON src/pokertool/cli.py gui
