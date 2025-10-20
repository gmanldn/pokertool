#!/bin/bash
# Launch Chrome with Remote Debugging for Poker Tool
# Usage: ./launch_chrome_debug.sh [port]

PORT=${1:-9222}
BETFAIR_URL="https://poker-com-ngm.bfcdl.com/poker"

echo "=========================================="
echo "Chrome Remote Debugging Launcher"
echo "=========================================="
echo ""
echo "Port: $PORT"
echo "URL: $BETFAIR_URL"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    PROFILE_DIR="/tmp/chrome-debug-profile"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CHROME_PATH="google-chrome"
    PROFILE_DIR="/tmp/chrome-debug-profile"
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "Please launch Chrome manually with:"
    echo "  chrome --remote-debugging-port=$PORT --user-data-dir=/tmp/chrome-debug-profile"
    exit 1
fi

# Check if Chrome exists
if [[ ! -e "$CHROME_PATH" ]] && ! command -v "$CHROME_PATH" &> /dev/null; then
    echo "❌ Chrome not found at: $CHROME_PATH"
    echo ""
    echo "Please install Chrome or update CHROME_PATH in this script"
    exit 1
fi

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port $PORT is already in use"
    echo ""
    read -p "Kill the process and continue? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PID=$(lsof -ti:$PORT)
        kill -9 $PID 2>/dev/null
        echo "✓ Killed process $PID"
        sleep 1
    else
        echo "❌ Aborted"
        exit 1
    fi
fi

# Launch Chrome
echo "🚀 Launching Chrome with remote debugging..."
echo ""

"$CHROME_PATH" \
    --remote-debugging-port=$PORT \
    --user-data-dir="$PROFILE_DIR" \
    "$BETFAIR_URL" \
    > /dev/null 2>&1 &

CHROME_PID=$!

# Wait a moment for Chrome to start
sleep 2

# Check if Chrome started successfully
if ps -p $CHROME_PID > /dev/null; then
    echo "✅ Chrome launched successfully!"
    echo ""
    echo "Chrome PID: $CHROME_PID"
    echo "Remote debugging: http://localhost:$PORT"
    echo ""
    echo "Next steps:"
    echo "  1. Log in to Betfair in the Chrome window"
    echo "  2. Join a poker table"
    echo "  3. Run the poker tool GUI:"
    echo "     python scripts/run_gui.py"
    echo "  4. Go to the LiveTable tab"
    echo ""
    echo "You should see: ⚡ CDP (< 20ms) in the status"
    echo ""
    echo "To test CDP connection:"
    echo "  python test_table_capture_diagnostic.py --live --cdp"
    echo ""
else
    echo "❌ Failed to launch Chrome"
    echo ""
    echo "Try launching manually:"
    echo "  $CHROME_PATH \\"
    echo "    --remote-debugging-port=$PORT \\"
    echo "    --user-data-dir=$PROFILE_DIR \\"
    echo "    $BETFAIR_URL"
    exit 1
fi
