#!/bin/bash
# Kill all pokertool-related processes

echo "Killing all pokertool processes..."

# Get list of PIDs
PIDS=$(ps aux | grep -E "python.*(pokertool|uvicorn|start\.py)" | grep -v grep | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "No processes found"
    exit 0
fi

echo "Found processes: $PIDS"

# Kill them all
for PID in $PIDS; do
    echo "Killing PID $PID"
    kill -9 $PID 2>/dev/null || true
done

echo "Done"
