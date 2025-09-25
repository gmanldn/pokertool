# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: start.py
# version: v20.0.0
# last_commit: '2025-09-23T08:41:38+01:00'
# fixes:
# - date: '2025-09-25'
#   summary: Enhanced enterprise documentation and comprehensive unit tests added
# ---
# POKERTOOL-HEADER-END
from __future__ import annotations
from pathlib import Path
from typing import Sequence
import os
import sys

import atexit
import shlex
import subprocess

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Try to import your logger; if missing, still run with a stub printed by repair script.
try:
    from logger import logger, log_exceptions, setup_global_exception_handler
except Exception as e:
    print('[start.py] WARN: failed to import logger.py: ', e, file=sys.stderr)
    def _noop(*_a, **_k):
        pass

    class _FakeLogger:
        """Fake logger for when real logger fails to import."""
        info = warning = error = critical = debug = staticmethod(_noop)

    logger = _FakeLogger()

    def log_exceptions(fn):
        """TODO: Add docstring."""
        return fn

    def setup_global_exception_handler():
        """TODO: Add docstring."""
        pass

def initialize_logging() -> None:
    """Initialize logging system."""
    setup_global_exception_handler()
    safe_env = {k: v for k, v in os.environ.items() if 'TOKEN' not in k and 'KEY' not in k}
    logger.info('APPLICATION STARTUP', argv=sys.argv, cwd=os.getcwd(), 
                python_path=list(sys.path), environment_vars=safe_env)

def cleanup() -> None:
    """Cleanup function called on exit."""
    logger.info('Performing cleanup')

def _log_cmd(args: list[str]) -> str:
    """Log command with proper shell escaping."""
    return ' '.join(shlex.quote(a) for a in args)

def _detect_scanner_flags(python: str, script: Path) -> dict[str, bool]:
    """
    Probe 'code_scan.py --help' and detect available flags.
    Returns a dict of supported flags (path, dry_run, no_backup).
    """
    supported = {'path': False, 'dry_run': False, 'no_backup': False}
    try:
        res = subprocess.run([python, str(script), '--help'], 
                           cwd=str(ROOT), capture_output=True, text=True)
        help_text = (res.stdout or '') + (res.stderr or '')
        ht = help_text.replace('-', '')
        supported['path'] = ('--path' in help_text) or (' path ' in ht)
        supported['dry_run'] = ('--dry-run' in help_text) or (' dry run' in ht)
        supported['no_backup'] = ('--no-backup' in help_text) or (' no backup' in ht)
        logger.debug('Scanner help detected', help=help_text)
    except Exception as e:
        logger.warning('Failed to probe code_scan.py --help', exception=e)
    return supported

def _internal_quick_syntax_scan(scan_path: Path) -> int:
    """
    Fallback: compile all .py files for syntax errors.
    Returns 0 on success, 1 if any errors occurred.
    """
    import py_compile
    import traceback

    errors = 0
    for p in scan_path.rglob('*.py'):
        # Skip common virtualenv / cache dirs
        parts = {part for part in p.parts}
        if any(x in parts for x in {'.venv', 'venv', '__pycache__', '.git'}):
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            logger.debug('Syntax OK', file=str(p))
        except Exception as e:
            errors += 1
            logger.error('Syntax error', file=str(p), exception=e)
            traceback.print_exc()

    if errors:
        logger.warning('Internal syntax scan found errors', count=errors)
        return 1
    logger.info('Internal syntax scan passed (no errors)')
    return 0

def run_code_scan(python: str, scan_path: Path) -> int:
    """
    Try to run ./code_scan.py. Auto-detect flags. If not present or failing,
    fallback to internal scan.
    Env overrides:
        START_NO_SCAN = 1        -> skip
        START_SCAN_DRY_RUN = 1   -> try dry-run if supported
        START_NO_BACKUP = 1      -> try no-backup if supported
        START_SCAN_PATH=...    -> override path
    """
    if os.environ.get('START_NO_SCAN') == '1':
        logger.info("Skipping preflight code scan due to START_NO_SCAN = 1")
        return 0

    script = ROOT / 'code_scan.py'
    if not script.exists():
        logger.warning("code_scan.py not found; using internal quick syntax scan")
        return _internal_quick_syntax_scan(scan_path)

    flags = _detect_scanner_flags(python, script)
    args = [python, str(script)]
    used_any = False

    # Prefer path if supported
    if flags['path']:
        args += ['--path', str(scan_path)]
        used_any = True

    # Optional flags gated by envs
    if os.environ.get('START_SCAN_DRY_RUN') == '1' and flags['dry_run']:
        args.append('--dry-run')
        used_any = True
    if os.environ.get('START_NO_BACKUP') == '1' and flags['no_backup']:
        args.append('--no-backup')
        used_any = True

    # If nothing was detected, still try a bare run; if that fails, use internal scan
    logger.info('Running code_scan.py', command=_log_cmd(args))
    completed = subprocess.run(args, cwd=str(ROOT))
    if completed.returncode != 0:
        logger.warning("code_scan.py non-zero or incompatible; running internal syntax scan",
                      returncode=completed.returncode)
        return _internal_quick_syntax_scan(scan_path)
    return 0

def launch_poker_go(python: str, passthrough_args: Sequence[str]) -> int:
    """
    Launch tools/poker_go.py with cwd = repo root and PYTHONPATH including repo root
    so 'from logger import ...' resolves when script lives under tools/.
    """
    poker_go = ROOT / 'tools' / 'poker_go.py'
    if not poker_go.exists():
        logger.critical('tools/poker_go.py not found', path=str(poker_go))
        return 2

    cmd = [python, str(poker_go), *passthrough_args]
    env = os.environ.copy()
    env['PYTHONPATH'] = f'{str(ROOT)}' + (os.pathsep + env['PYTHONPATH'] if 'PYTHONPATH' in env else '')
    logger.info('Launching poker_go.py', command=_log_cmd(cmd), PYTHONPATH=env.get('PYTHONPATH'))
    completed = subprocess.run(cmd, cwd=str(ROOT), env=env)
    return int(completed.returncode)

@log_exceptions
def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the application."""
    argv = list(argv or sys.argv[1:])
    initialize_logging()

    # Defaults
    scan_path = Path(os.environ.get('START_SCAN_PATH', str(ROOT))).resolve()
    passthrough: list[str] = []

    # Minimal passthrough arg split: everything after '--' goes to poker_go.py
    while argv:
        a = argv.pop(0)
        if a == '--scan-path' and argv:
            scan_path = Path(argv.pop(0)).resolve()
        elif a == '--':
            passthrough = argv[:]
            break
        else:
            passthrough.append(a)

    rc = run_code_scan(sys.executable, scan_path)
    if rc != 0:
        logger.warning('Proceeding despite scan issues', returncode=rc)

    try:
        logger.info('Starting poker tool application')
        test_value = {'cards': ["As", "Kh"], 'position': 'BTN'}
        logger.debug('Test debug message', test_data=test_value)
        app_rc = launch_poker_go(sys.executable, passthrough)
    except Exception as e:
        logger.critical('Application failed to start', exception=e)
        return 1

    logger.info('Application shutdown', returncode=app_rc)
    return app_rc

if __name__ == '__main__':
    atexit.register(cleanup)
    raise SystemExit(main())
