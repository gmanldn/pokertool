from __future__ import annotations
"""
Legacy GUI shim. Use `pokertool` CLI going forward.
"""
def main() -> int:
    try:
        from pokertool.gui import main as gui_main  # type: ignore
    except Exception:
        from pokertool.gui import run as gui_main  # type: ignore
    return gui_main()

if __name__ == "__main__":
    raise SystemExit(main())
