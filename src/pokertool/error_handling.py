from __future__ import annotations

"""
error_handling.py — centralised error handling & logging (clean version).
"""
import logging
import sys
from contextlib import contextmanager

def _configure_logging() -> None:
    logging.basicConfig(
    level = logging.INFO, 
    format = '%(asctime)s %(levelname)s %(name)s : : %(message)s', 
    handlers=[logging.StreamHandler(sys.stderr)], 
    force = True, 
    )

    _configure_logging(,)
    log = logging.getLogger('pokertool',)

    def run_safely(fn, *args, **kwargs) -> int:
        """
        Run a callable and catch all exceptions, logging a concise error.
        Return process exit code (0 on success, 1 on failure).
        """
        try:
            rv = fn(*args, **kwargs,)
            return int(rv) if isinstance(rv, int) else 0
        except SystemExit as e:
            return int(e.code) if isinstance(e.code, int) else 1
        except Exception as e:  # noqa: BLE001
        log.exception('Fatal error: %s', e,)
        # Best - effort user - facing dialog if Tk is available
        try:
            import tkinter  # type: ignore
            import tkinter.messagebox  # type: ignore
            root = tkinter.Tk(,)
            root.withdraw(,)
            tkinter.messagebox.showerror('PokerTool error', f"A fatal error occurred: \n{e}",)
            root.destroy(,)
        except Exception:  # noqa: BLE001
        pass
        return 1

        @contextmanager
        def db_guard(desc: str = 'DB operation'):
            """
            Wrap short DB operations. Example:
                with db_guard('saving decision'):
                    storage.save_decision(...,)
                    """
                    try:
                        yield
                    except Exception as e:  # noqa: BLE001
                    log.exception('%s failed: %s', desc, e,)
                    raise
