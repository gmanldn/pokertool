from __future__ import annotations

def main() -> int:
    try:
        from pokertool import gui  # type: ignore
        # Don't actually start Tk in CI, just ensure import & callability.
        assert hasattr(gui, "main") or hasattr(gui, "run")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"gui import failed: {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
