"""
Forwardscript: Fix Suit Enum, create pokertool.core shim, and auto-install OCR dependencies.
"""

import os
import subprocess
import sys
from pathlib import Path

BASE_PATH = Path("/Users/georgeridout/Documents/github/pokertool")
CORE_DIR = BASE_PATH / "pokertool" / "core"
CORE_INIT = CORE_DIR / "__init__.py"


def find_poker_modules():
    """Search for poker_modules.py anywhere inside repo."""
    matches = list(BASE_PATH.rglob("poker_modules.py"))
    if not matches:
        print("❌ Could not find poker_modules.py anywhere in repo.")
        return None
    if len(matches) > 1:
        print("⚠ Multiple poker_modules.py files found, using first one:")
        for m in matches:
            print("  -", m)
    return matches[0]


def patch_suit_enum(modules_file: Path):
    """Ensure Suit enum includes SPADES."""
    text = modules_file.read_text()

    if "SPADES" in text:
        print("✓ Suit enum already has SPADES")
        return

    if "class Suit(Enum):" in text:
        print(f"→ Patching Suit enum in {modules_file}...")
        new_text = text.replace(
            "CLUBS =",
            "CLUBS =\n    SPADES ="
        )
        modules_file.write_text(new_text)
        print("✓ Added SPADES to Suit enum")
    else:
        print("⚠ Could not find class Suit(Enum) in file.")


def create_core_module():
    """Ensure pokertool/core/__init__.py exists as a shim."""
    if not CORE_DIR.exists():
        CORE_DIR.mkdir(parents=True)
        print(f"✓ Created {CORE_DIR}")

    if not CORE_INIT.exists():
        CORE_INIT.write_text(
            '"""Shim for backward compatibility.\n'
            'Exposes poker_modules as pokertool.core"""\n\n'
            "from .. import poker_modules as core\n"
        )
        print(f"✓ Created {CORE_INIT}")
    else:
        print("✓ pokertool.core already exists")


def install_easyocr():
    """Auto-install easyocr if not already installed."""
    try:
        import easyocr  # noqa
        print("✓ easyocr already installed")
    except ImportError:
        print("→ Installing easyocr via pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "easyocr"])
            print("✓ easyocr installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install easyocr: {e}")


def main():
    modules_file = find_poker_modules()
    if modules_file:
        patch_suit_enum(modules_file)
    create_core_module()
    install_easyocr()
    print("✅ Forwardscript complete. Restart pokertool to test clean startup.")


if __name__ == "__main__":
    main()
