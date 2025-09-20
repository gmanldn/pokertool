"""
pokertool package — stable API surface.
"""
# Re-export commonly-used symbols if present in core.
try:
    from .core import analyse_hand, Card  # type: ignore[attr-defined]
except Exception:
    # If not present, expose nothing; users / tests can still import .core directly.
    pass
