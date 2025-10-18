"""
Python package wrapper for the repository's source tree.

Some of the higher-level tests import modules using the `src.pokertool`
namespace. Adding this module makes `src` a proper package while avoiding side
effects at import time.
"""

from __future__ import annotations

# Intentionally empty: this package only exists so that `import src.pokertool`
# resolves correctly in environments where the repository root is on
# PYTHONPATH.
