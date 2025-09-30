#!/bin/bash
# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: activate_pokertool.sh
# version: v28.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END

# Set NumExpr thread limit to prevent warning
export NUMEXPR_MAX_THREADS=8

echo "Activating pokertool environment..."
source "/Users/georgeridout/Documents/github/pokertool/venv/bin/activate"
echo "Environment activated. ONNX Runtime conflicts resolved."
echo "NumExpr max threads set to 8."
echo "You can now run: python start.py"
exec "$SHELL"
