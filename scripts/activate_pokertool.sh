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

# Check and install critical dependencies upfront
echo ""
echo "Checking critical dependencies..."
python3 -c "
import subprocess
import sys
from distutils.version import LooseVersion

critical_deps = [
    ('cv2', 'opencv-python'),
    ('PIL', 'Pillow'),
    ('pytesseract', 'pytesseract'),
]

missing = []
for module_name, package_name in critical_deps:
    try:
        __import__(module_name)
        print(f'✅ {package_name} is available')
    except ImportError:
        missing.append(package_name)
        print(f'❌ {package_name} is MISSING')

optional_note = "Optional ML accelerators (install manually if needed): torch>=2.0.0,<3.0.0"

if missing:
    print(f'\n📦 Installing missing dependencies...')
    for package in missing:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f'✅ {package} installed')
        except Exception as e:
            print(f'⚠️  Failed to install {package}: {e}')
else:
    print('\n✅ All critical dependencies are available')

print(f'\nℹ️ {optional_note}')
"

echo ""
echo "You can now run: python scripts/start.py or python -m pokertool.modules.run_pokertool"
echo "Run tests with: python scripts/run_tests.py"
exec "$SHELL"
