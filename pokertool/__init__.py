"""Compat shim so the in-repo sources resolve without manual PYTHONPATH tweaks."""

from __future__ import annotations

from pathlib import Path
import sys


_PKG_DIR = Path(__file__).resolve().parent
_SRC_ROOT = _PKG_DIR.parent / 'src'
_SRC_PACKAGE = _SRC_ROOT / __name__
_MODULES_DIR = _PKG_DIR / 'modules'

if _SRC_PACKAGE.exists():
    src_pkg_path = str(_SRC_PACKAGE)
    if src_pkg_path not in __path__:
        __path__.append(src_pkg_path)

    src_root_path = str(_SRC_ROOT)
    if src_root_path not in sys.path:
        # Ensure direct, relative imports keep working when executed from repo root
        sys.path.insert(0, src_root_path)

if _MODULES_DIR.exists():
    modules_path = str(_MODULES_DIR)
    if modules_path not in sys.path:
        sys.path.insert(0, modules_path)
