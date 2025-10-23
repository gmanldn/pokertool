#!/bin/bash
# Restart the PokerTool application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/update_manager.py" restart
