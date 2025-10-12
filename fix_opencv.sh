#!/bin/bash
# Fix OpenCV loading issue on macOS

echo "======================================================================"
echo "FIXING OPENCV INSTALLATION"
echo "======================================================================"
echo ""

echo "Removing problematic opencv-python..."
./.venv/bin/pip uninstall -y opencv-python 2>/dev/null

echo "Installing opencv-python-headless (works better on macOS)..."
./.venv/bin/pip install opencv-python-headless

echo ""
echo "Testing OpenCV import..."
if ./.venv/bin/python -c "import cv2; print(f'✓ OpenCV {cv2.__version__} working!')" 2>/dev/null; then
    echo ""
    echo "======================================================================"
    echo "✓ OPENCV FIXED!"
    echo "======================================================================"
    echo ""
    echo "You can now run: python start.py"
    exit 0
else
    echo ""
    echo "======================================================================"
    echo "⚠ OpenCV still having issues"
    echo "======================================================================"
    echo ""
    echo "Try installing via Homebrew:"
    echo "  brew install opencv"
    echo ""
    echo "Or check: https://github.com/opencv/opencv-python/issues"
    exit 1
fi
