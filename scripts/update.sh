#!/bin/bash
# Pull latest changes and rebuild frontend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/update_manager.py" update
