# POKERTOOL-HEADER-START
# ---
# schema: pokerheader.v1
# project: pokertool
# file: start.py
# version: v28.0.0
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

SRC_DIR = ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

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


def _build_launcher_env() -> dict[str, str]:
    """Construct environment with repo paths prioritized for subprocess launches."""
    env = os.environ.copy()
    pythonpath_entries = [str(ROOT), str(SRC_DIR)]
    existing = env.get('PYTHONPATH')
    if existing:
        pythonpath_entries.extend(p for p in existing.split(os.pathsep) if p)

    deduped: list[str] = []
    seen: set[str] = set()
    for entry in pythonpath_entries:
        if entry not in seen:
            deduped.append(entry)
            seen.add(entry)

    env['PYTHONPATH'] = os.pathsep.join(deduped)
    return env


def _launch_via_module(passthrough_args: Sequence[str]) -> int:
    """Launch PokerTool via `python -m pokertool` to favor the packaged entry point."""
    env = _build_launcher_env()
    cmd = [sys.executable, '-m', 'pokertool', *passthrough_args]
    logger.info('Launching pokertool via module', command=_log_cmd(cmd))
    completed = subprocess.run(cmd, cwd=str(ROOT), env=env)
    if completed.returncode == 0:
        return 0

    logger.warning(
        'Module launcher returned non-zero; falling back to legacy script discovery',
        returncode=completed.returncode
    )
    return _launch_via_fallback_scripts(passthrough_args, env=env)


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

def run_code_scan(python: str, scan_path: Path, *, quick: bool = True, auto_fix: bool = True) -> int:
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

    dry_run_requested = os.environ.get('START_SCAN_DRY_RUN') == '1'
    no_backup_requested = os.environ.get('START_NO_BACKUP') == '1'

    try:
        import code_scan  # type: ignore

        if hasattr(code_scan, 'scan_and_fix'):
            logger.info(
                'Running code_scan.scan_and_fix via import',
                quick=quick,
                auto_fix=auto_fix,
                dry_run=dry_run_requested,
                no_backup=no_backup_requested,
                scan_path=str(scan_path)
            )
            kwargs = {
                'root': ROOT,
                'quick': quick,
                'auto_fix': auto_fix,
            }
            if scan_path:
                kwargs['path'] = str(scan_path)
            if dry_run_requested:
                kwargs['dry_run'] = True
            if no_backup_requested:
                kwargs['no_backup'] = True

            try:
                result = code_scan.scan_and_fix(**kwargs)  # type: ignore[attr-defined]
            except TypeError:
                # Older implementations may not accept optional keywords
                result = code_scan.scan_and_fix(  # type: ignore[attr-defined]
                    ROOT,
                    quick=quick,
                    auto_fix=auto_fix,
                )
            errs = getattr(result, 'errors', None)
            fixed = getattr(result, 'fixed', None)
            if errs is not None or fixed is not None:
                logger.info('Code scan finished', errors=errs, fixed=fixed)
            return 0

        if hasattr(code_scan, 'main'):
            args = ['--root', str(ROOT)]
            if scan_path and scan_path != ROOT:
                args += ['--path', str(scan_path)]
            args.append('--autofix' if auto_fix else '--no-autofix')
            args.append('--quick' if quick else '--full')
            if dry_run_requested:
                args.append('--dry-run')
            if no_backup_requested:
                args.append('--no-backup')

            logger.info('Running code_scan.main via import', args=args)
            return int(code_scan.main(args))  # type: ignore[attr-defined]

    except Exception as e:
        logger.warning('Importing code_scan failed; falling back to subprocess', exception=e)

    script = ROOT / 'code_scan.py'
    if not script.exists():
        logger.warning("code_scan.py not found; using internal quick syntax scan")
        return _internal_quick_syntax_scan(scan_path)

    flags = _detect_scanner_flags(python, script)
    args = [python, str(script)]

    if flags['path']:
        args += ['--path', str(scan_path)]

    args.append('--autofix' if auto_fix else '--no-autofix')
    args.append('--quick' if quick else '--full')

    if dry_run_requested and flags['dry_run']:
        args.append('--dry-run')
    if no_backup_requested and flags['no_backup']:
        args.append('--no-backup')

    logger.info('Running code_scan.py', command=_log_cmd(args))
    completed = subprocess.run(args, cwd=str(ROOT))
    if completed.returncode != 0:
        logger.warning(
            "code_scan.py non-zero or incompatible; running internal syntax scan",
            returncode=completed.returncode
        )
        return _internal_quick_syntax_scan(scan_path)
    return 0

def _launch_cli_directly(passthrough_args: Sequence[str]) -> int:
    """Attempt to launch the PokerTool CLI directly inside the current process."""
    try:
        from pokertool import cli as cli_module
    except ImportError as e:
        logger.warning('Direct CLI import failed; retrying via module launcher', exception=e)
        return _launch_via_module(passthrough_args)

    try:
        logger.info('Launching pokertool.cli directly')
        return int(cli_module.main(list(passthrough_args)))
    except Exception as e:
        logger.warning('pokertool.cli execution error; retrying via module launcher', exception=e)
        return _launch_via_module(passthrough_args)


def _launch_via_fallback_scripts(
    passthrough_args: Sequence[str], *, env: dict[str, str] | None = None
) -> int:
    """Fallback: try to execute known launcher scripts via subprocess."""
    candidate_scripts = [
        ROOT / 'src' / 'pokertool' / 'cli.py',
        ROOT / 'tools' / 'poker_go.py',
        ROOT / 'tools' / 'enhanced_poker_gui.py',
        ROOT / 'launch_pokertool.py',
    ]

    launch_env = env or _build_launcher_env()

    for script in candidate_scripts:
        if script.exists():
            cmd = [sys.executable, str(script), *passthrough_args]
            logger.info('Launching fallback script', command=_log_cmd(cmd), script=str(script))
            completed = subprocess.run(cmd, cwd=str(ROOT), env=launch_env)
            return int(completed.returncode)

    logger.warning('No executable fallback launcher found', candidates=[str(p) for p in candidate_scripts])
    return 0

@log_exceptions
def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point for the application."""
    argv = list(argv or sys.argv[1:])
    initialize_logging()

    try:
        from pokertool.automation import ensure_ml_tests_run
    except Exception as exc:  # pragma: no cover - defensive import guard
        logger.warning('Unable to load automation helpers', exception=exc)
    else:
        try:
            ensure_ml_tests_run(logger)
        except Exception as exc:  # pragma: no cover - defensive execution guard
            logger.warning('ML auto-test execution failed', exception=exc)

    # Defaults
    scan_path = Path(os.environ.get('START_SCAN_PATH', str(ROOT))).resolve()
    run_scan = True
    quick_scan = True
    auto_fix = True
    passthrough: list[str] = []

    # Minimal passthrough arg split: everything after '--' goes to poker_go.py
    while argv:
        a = argv.pop(0)
        if a == '--scan-path' and argv:
            scan_path = Path(argv.pop(0)).resolve()
        elif a == '--no-scan':
            run_scan = False
        elif a == '--no-fix':
            auto_fix = False
        elif a == '--full-scan':
            quick_scan = False
        elif a == '--':
            passthrough = argv[:]
            break
        else:
            passthrough.append(a)

    if run_scan:
        rc = run_code_scan(sys.executable, scan_path, quick=quick_scan, auto_fix=auto_fix)
        if rc != 0:
            logger.warning('Proceeding despite scan issues', returncode=rc)
    else:
        logger.info('Skipping preflight scan (requested via flag)')

    try:
        logger.info('Starting poker tool application')
        test_value = {'cards': ["As", "Kh"], 'position': 'BTN'}
        logger.debug('Test debug message', test_data=test_value)
        app_rc = _launch_cli_directly(passthrough)
    except Exception as e:
        logger.critical('Application failed to start', exception=e)
        return 1

    logger.info('Application shutdown', returncode=app_rc)
    return app_rc

if __name__ == '__main__':
    atexit.register(cleanup)
    raise SystemExit(main())
