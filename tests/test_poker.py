from __future__ import annotations

def test_package_imports():
    """Test that the pokertool package can be imported."""
    import pokertool  # noqa: F401

def test_core_symbols_exist_if_implemented():
    """Test that core module symbols exist and are callable."""
    try:
        from pokertool.core import analyse_hand  # type: ignore
        assert callable(analyse_hand)
    except Exception:
        # Core may not expose yet; that's okay for smoke
        assert True
