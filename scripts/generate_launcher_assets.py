#!/usr/bin/env python3
"""Generate platform launcher icon assets from the base project icon."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


BASE_ICON = Path(__file__).resolve().parents[1] / "assets" / "icons" / "icon.png"
MAC_ICONSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "launchers" / "macos" / "AppIcon.iconset"
WINDOWS_DIR = Path(__file__).resolve().parents[1] / "assets" / "launchers" / "windows"


def ensure_base_icon() -> Image.Image:
    """Load the project base icon."""
    if not BASE_ICON.exists():
        raise FileNotFoundError(f"Base icon not found: {BASE_ICON}")
    return Image.open(BASE_ICON)


def generate_macos_iconset(base_icon: Image.Image) -> None:
    """Populate the macOS .iconset directory with required sizes."""
    MAC_ICONSET_DIR.mkdir(parents=True, exist_ok=True)
    sizes = [16, 32, 64, 128, 256, 512]

    for size in sizes:
        resized = base_icon.resize((size, size), Image.LANCZOS)
        resized.save(MAC_ICONSET_DIR / f"icon_{size}x{size}.png")

        if size != 512:
            retina = base_icon.resize((size * 2, size * 2), Image.LANCZOS)
            retina.save(MAC_ICONSET_DIR / f"icon_{size}x{size}@2x.png")


def generate_windows_icon(base_icon: Image.Image) -> None:
    """Create a multi-resolution .ico file for Windows launchers."""
    WINDOWS_DIR.mkdir(parents=True, exist_ok=True)
    ico_path = WINDOWS_DIR / "pokertool.ico"
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base_icon.save(ico_path, sizes=sizes)


def main() -> int:
    """Generate launcher assets for macOS and Windows."""
    base_icon = ensure_base_icon()
    generate_macos_iconset(base_icon)
    generate_windows_icon(base_icon)
    print("Launcher assets regenerated.")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI utility
    raise SystemExit(main())
