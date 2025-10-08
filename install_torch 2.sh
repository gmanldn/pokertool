#!/bin/bash
# POKERTOOL Torch Installation Script
# Handles PyTorch installation for Python 3.13+ compatibility issues

set -e

echo "🔥 POKERTOOL Torch Installation Script"
echo "======================================"
echo ""

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "❌ Virtual environment not activated!"
    echo "Please run: source .venv/bin/activate"
    exit 1
fi

echo "✅ Virtual environment detected: $VIRTUAL_ENV"
echo "🐍 Python version: $(python --version)"
echo ""

# Check Python version
PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🔍 Python version detected: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" == "3.13" ]]; then
    echo ""
    echo "⚠️  Python 3.13 detected - PyTorch doesn't have pre-built wheels yet"
    echo "🔧 Trying alternative installation methods..."
    echo ""
    
    # Method 1: Try nightly builds (may have Python 3.13 support)
    echo "📦 Method 1: Trying PyTorch nightly builds..."
    if pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu; then
        echo "✅ Successfully installed PyTorch nightly build!"
        exit 0
    else
        echo "❌ Nightly build failed"
    fi
    
    # Method 2: Try installing from source (CPU only)
    echo ""
    echo "📦 Method 2: Installing minimal CPU-only version..."
    if pip install torch --no-deps --force-reinstall; then
        echo "✅ Basic torch installation successful"
        echo "⚠️  Note: This may have limited functionality"
    else
        echo "❌ Basic installation failed"
        echo ""
        echo "💡 RECOMMENDED SOLUTIONS:"
        echo "1. Use Python 3.11 or 3.12 for full PyTorch compatibility"
        echo "2. Wait for official PyTorch Python 3.13 wheels"
        echo "3. For now, torch has been disabled in requirements.txt"
        exit 1
    fi
    
else
    echo "✅ Python $PYTHON_VERSION is supported by PyTorch"
    echo "📦 Installing PyTorch with CPU support..."
    
    if pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu; then
        echo "✅ PyTorch installation successful!"
    else
        echo "❌ PyTorch installation failed"
        exit 1
    fi
fi

echo ""
echo "🧪 Testing PyTorch installation..."
if python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print('✅ PyTorch working correctly!')"; then
    echo "✅ All tests passed!"
else
    echo "❌ PyTorch test failed"
    exit 1
fi

echo ""
echo "🎉 PyTorch installation completed successfully!"
echo "💡 You can now uncomment the torch line in requirements.txt if needed"
