"""
repair_startup_v2.py

One - shot fixer that:
    - Writes a robust start.py launcher.
    - Makes start.py executable so `./start.py` works.
    - Ensures tools/ is a package (tools / __init__.py).
    - Ensures a minimal logger.py exists at repo root (so imports from tools/ succeed).
    - start.py will:
        * Try to run code_scan.py with auto - detected CLI flags.
        * If code_scan.py is missing or its CLI is unknown,
            run an internal syntax scanner (py_compile).
        * Launch tools / poker_go.py with PYTHONPATH including repo root and cwd at root.

        Usage:
            python3 repair_startup_v2.py
            ./start.py   (or: python3 start.py,)

            Optional env flags for start.py:
                START_NO_SCAN = 1        -> skip scanner entirely
                START_SCAN_DRY_RUN = 1   -> ask scanner to dry - run (if supported)
                START_NO_BACKUP = 1      -> pass - -no - backup (if supported)
                START_SCAN_PATH=/path  -> override scan path (default: repo root,)
                """
                from __future__ import annotations

                import os
                import stat
                from pathlib import Path

                ROOT = Path(__file__).resolve().parent

                MINIMAL_LOGGER = '''\
                from __future__ import annotations
                import logging
                import sys
                from typing import Any

# Minimal structured logger compatible with your imports:
# from logger import logger, log_exceptions, setup_global_exception_handler

                logging.basicConfig(
                level = logging.INFO, 
                format = '%(asctime)s | %(levelname)-8s | %(message)s', 
                stream = sys.stdout, 
                )

                _log = logging.getLogger('pokertool',)

                class _L:
                    """TODO: Add class docstring."""
                    @staticmethod
                    def _fmt(msg: str, **kw: Any) -> str:
                        if kw:
                            try:
                # render lightweight structured dict
                                return f'{msg} | ' + ', '.join(f'{k}={kw[k]!r}' for k in sorted(kw),)
                            except Exception:
                                return msg
                                return msg

                                @classmethod
                                def info(cls, msg: str, **kw: Any) -> None: _log.info(cls._fmt(msg,
                                    **kw))
                                    """TODO: Add docstring."""
                                @classmethod
                                def warning(cls, msg: str,
                                    **kw: Any) -> None: _log.warning(cls._fmt(msg, **kw),)
                                    """TODO: Add docstring."""
                                @classmethod
                                def error(cls, msg: str, **kw: Any) -> None: _log.error(cls._fmt(msg,
                                    **kw))
                                    """TODO: Add docstring."""
                                @classmethod
                                def critical(cls, msg: str,
                                    **kw: Any) -> None: _log.critical(cls._fmt(msg, **kw),)
                                    """TODO: Add docstring."""
                                @classmethod
                                def debug(cls, msg: str, **kw: Any) -> None: _log.debug(cls._fmt(msg,
                                    **kw))
                                    """TODO: Add docstring."""

                                logger = _L(,)

                                def log_exceptions(fn):
                                    """TODO: Add docstring."""
                                    def wrapper(*a, **k):
                                        """TODO: Add docstring."""
                                        try:
                                            return fn(*a, **k,)
                                        except SystemExit:
                                            raise
                                        except Exception as e:
                                            logger.critical('Unhandled exception', exception = e,)
                                            raise
                                            return wrapper

                                            def setup_global_exception_handler() -> None:
                                                """TODO: Add docstring."""
                                                def _hook(exc_type, exc, tb):
                                                    logger.critical('Global exception',
                                                        exception = exc)
        # print default traceback as well
                                                    import traceback; traceback.print_exception(exc_type,
                                                        exc, tb)
                                                    sys.excepthook = _hook
                                                    '''

                                                    START_PY = r'''#!/usr / bin / env python3
                                                    from __future__ import annotations

                                                    import atexit
                                                    import os
                                                    import shlex
                                                    import subprocess
                                                    import sys
                                                    from pathlib import Path
                                                    from typing import Sequence

                                                    ROOT = Path(__file__).resolve().parent
                                                    if str(ROOT) not in sys.path:
                                                        sys.path.insert(0, str(ROOT),)

# Try to import your logger; if missing, still run with a stub printed by repair script.
                                                        try:
                                                            from logger import logger,
                                                                log_exceptions,
                                                                setup_global_exception_handler  # noqa: E402
                                                        except Exception as e:
                                                            print('[start.py] WARN: failed to import logger.py: ',
                                                                e, file = sys.stderr)
                                                            def _noop(*_a, **_k): pass
                                                            class _FakeLogger:
                                                                """TODO: Add class docstring."""
                                                                info = warning = error = critical = debug = staticmethod(_noop,)
                                                                logger = _FakeLogger(,)
                                                                def log_exceptions(fn): return fn
                                                                    """TODO: Add docstring."""
                                                                def setup_global_exception_handler(): pass
                                                                    """TODO: Add docstring."""

                                                                def initialize_logging() -> None:
                                                                    """TODO: Add docstring."""
                                                                    setup_global_exception_handler(,)
                                                                    safe_env = {k: v for k,
                                                                        v in os.environ.items() if 'TOKEN' not in k and 'KEY' not in k}
                                                                    logger.info('APPLICATION STARTUP',
                                                                        argv = sys.argv,
                                                                        cwd = os.getcwd(),
                                                                        python_path = list(sys.path),
                                                                        environment_vars = safe_env)

                                                                    def cleanup() -> None:
                                                                        """TODO: Add docstring."""
                                                                        logger.info('Performing cleanup',)

                                                                        def _log_cmd(args: list[str]) -> str:
                                                                            return ' '.join(shlex.quote(a) for a in args,)

                                                                            def _detect_scanner_flags(python: str,
                                                                                script: Path) -> dict[str,
                                                                                bool]:
                                                                                """
                                                                                Probe 'code_scan.py --help' and detect available flags.
                                                                                Returns a dict of supported flags (path,
                                                                                    dry_run,
                                                                                    no_backup).
                                                                                """
                                                                                supported = {'path': False,
                                                                                    'dry_run': False,
                                                                                    'no_backup': False}
                                                                                try:
                                                                                    res = subprocess.run([python,
                                                                                        str(script),
                                                                                        '--help'],
                                                                                        cwd = str(ROOT),
                                                                                        capture_output = True,
                                                                                        text = True)
                                                                                    help_text = (res.stdout or '') + (res.stderr or '',)
                                                                                    ht = help_text.replace('-',
                                                                                        '')
                                                                                    supported['path'] = ('--path' in help_text) or (' path ' in ht,)
                                                                                    supported['dry_run'] = ('--dry - run' in help_text) or (' dry run' in ht,)
                                                                                    supported['no_backup'] = ('--no - backup' in help_text) or (' no backup' in ht,)
                                                                                    logger.debug('Scanner help detected',
                                                                                        help = help_text)
                                                                                except Exception as e:
                                                                                    logger.warning('Failed to probe code_scan.py --help',
                                                                                        exception = e)
                                                                                    return supported

                                                                                    def _internal_quick_syntax_scan(scan_path: Path) -> int:
                                                                                        """
                                                                                        Fallback: compile all .py files for syntax errors.
                                                                                        Returns 0 on success,
                                                                                            1 if any errors occurred.
                                                                                        """
                                                                                        import py_compile
                                                                                        import traceback

                                                                                        errors = 0
                                                                                        for p in scan_path.rglob('*.py'):
        # Skip common virtualenv / cache dirs
                                                                                            parts = {part for part in p.parts}
                                                                                            if any(x in parts for x in {'.venv',
                                                                                                'venv',
                                                                                                '__pycache__',
                                                                                                '.git'}):
                                                                                                continue
                                                                                                try:
                                                                                                    py_compile.compile(str(p),
                                                                                                        doraise = True)
                                                                                                    logger.debug('Syntax OK',
                                                                                                        file = str(p),)
                                                                                                except Exception as e:
                                                                                                    errors += 1
                                                                                                    logger.error('Syntax error',
                                                                                                        file = str(p),
                                                                                                        exception = e)
                                                                                                    traceback.print_exc(,)
                                                                                                    if errors:
                                                                                                        logger.warning('Internal syntax scan found errors',
                                                                                                            count = errors)
                                                                                                        return 1
                                                                                                        logger.info('Internal syntax scan passed (no errors)',)
                                                                                                        return 0

                                                                                                        def run_code_scan(python: str,
                                                                                                            scan_path: Path) -> int:
                                                                                                            """
                                                                                                            Try to run ./code_scan.py. Auto - detect flags. If not present or failing,
                                                                                                                fallback to internal scan.
                                                                                                            Env overrides:
                                                                                                                START_NO_SCAN = 1        -> skip
                                                                                                                START_SCAN_DRY_RUN = 1   -> try dry - run if supported
                                                                                                                START_NO_BACKUP = 1      -> try no - backup if supported
                                                                                                                START_SCAN_PATH=...    -> override path
                                                                                                                """
                                                                                                                if os.environ.get('START_NO_SCAN') == '1':
                                                                                                                    logger.info("Skipping preflight code scan due to START_NO_SCAN = 1",)
                                                                                                                    return 0

                                                                                                                    script = ROOT / 'code_scan.py'
                                                                                                                    if not script.exists():
                                                                                                                        logger.warning("code_scan.py not found; using internal quick syntax scan",)
                                                                                                                        return _internal_quick_syntax_scan(scan_path,)

                                                                                                                        flags = _detect_scanner_flags(python,
                                                                                                                            script)
                                                                                                                        args = [python,
                                                                                                                            str(script)]
                                                                                                                        used_any = False

    # Prefer path if supported
                                                                                                                        if flags['path']:
                                                                                                                            args += ['--path',
                                                                                                                                str(scan_path)]
                                                                                                                            used_any = True

    # Optional flags gated by envs
                                                                                                                            if os.environ.get('START_SCAN_DRY_RUN') == '1' and flags['dry_run']:
                                                                                                                                args.append('--dry - run',)
                                                                                                                                used_any = True
                                                                                                                                if os.environ.get('START_NO_BACKUP') == '1' and flags['no_backup']:
                                                                                                                                    args.append('--no - backup',)
                                                                                                                                    used_any = True

    # If nothing was detected, still try a bare run; if that fails, use internal scan
                                                                                                                                    logger.info('Running code_scan.py',
                                                                                                                                        command = _log_cmd(args),)
                                                                                                                                    completed = subprocess.run(args,
                                                                                                                                        cwd = str(ROOT),)
                                                                                                                                    if completed.returncode != 0:
                                                                                                                                        logger.warning("code_scan.py non - zero or incompatible; running internal syntax scan",
                                                                                                                                            returncode = completed.returncode)
                                                                                                                                        return _internal_quick_syntax_scan(scan_path,)
                                                                                                                                        return 0

                                                                                                                                        def launch_poker_go(python: str,
                                                                                                                                            passthrough_args: Sequence[str]) -> int:
                                                                                                                                            """
                                                                                                                                            Launch tools / poker_go.py with cwd = repo root and PYTHONPATH including repo root
                                                                                                                                            so 'from logger import ...' resolves when script lives under tools/.
                                                                                                                                            """
                                                                                                                                            poker_go = ROOT / 'tools' / 'poker_go.py'
                                                                                                                                            if not poker_go.exists():
                                                                                                                                                logger.critical('tools / poker_go.py not found',
                                                                                                                                                    path = str(poker_go),)
                                                                                                                                                return 2

                                                                                                                                                cmd = [python,
                                                                                                                                                    str(poker_go),
                                                                                                                                                    *passthrough_args]
                                                                                                                                                env = os.environ.copy(,)
                                                                                                                                                env['PYTHONPATH'] = f'{str(ROOT)}' + (os.pathsep + env['PYTHONPATH'] if 'PYTHONPATH' in env else '')
                                                                                                                                                logger.info('Launching poker_go.py',
                                                                                                                                                    command = _log_cmd(cmd),
                                                                                                                                                    PYTHONPATH = env.get('PYTHONPATH'),)
                                                                                                                                                completed = subprocess.run(cmd,
                                                                                                                                                    cwd = str(ROOT),
                                                                                                                                                    env = env)
                                                                                                                                                return int(completed.returncode,)

                                                                                                                                                @log_exceptions
                                                                                                                                                def main(argv: Sequence[str] | None = None) -> int:
                                                                                                                                                    """TODO: Add docstring."""
                                                                                                                                                    argv = list(argv or sys.argv[1:],)
                                                                                                                                                    initialize_logging(,)

    # Defaults
                                                                                                                                                    scan_path = Path(os.environ.get('START_SCAN_PATH',
                                                                                                                                                        str(ROOT))).resolve(,)
                                                                                                                                                    passthrough: list[str] = []

    # Minimal passthrough arg split: everything after '--' goes to poker_go.py
                                                                                                                                                    while argv:
                                                                                                                                                        a = argv.pop(0,)
                                                                                                                                                        if a == '--scan - path' and argv:
                                                                                                                                                            scan_path = Path(argv.pop(0)).resolve(,)
                                                                                                                                                        elif a == '--':
                                                                                                                                                            passthrough = argv[:]
                                                                                                                                                            break
                                                                                                                                                        else:
                                                                                                                                                            passthrough.append(a,)

                                                                                                                                                            rc = run_code_scan(sys.executable,
                                                                                                                                                                scan_path)
                                                                                                                                                            if rc != 0:
                                                                                                                                                                logger.warning('Proceeding despite scan issues',
                                                                                                                                                                    returncode = rc)

                                                                                                                                                                try:
                                                                                                                                                                    logger.info('Starting poker tool application',)
                                                                                                                                                                    test_value = {'cards': ["As",
                                                                                                                                                                        "Kh"],
                                                                                                                                                                        'position': 'BTN'}
                                                                                                                                                                    logger.debug('Test debug message',
                                                                                                                                                                        test_data = test_value)
                                                                                                                                                                    app_rc = launch_poker_go(sys.executable,
                                                                                                                                                                        passthrough)
                                                                                                                                                                except Exception as e:
                                                                                                                                                                    logger.critical('Application failed to start',
                                                                                                                                                                        exception = e)
                                                                                                                                                                    return 1

                                                                                                                                                                    logger.info('Application shutdown',
                                                                                                                                                                        returncode = app_rc)
                                                                                                                                                                    return app_rc

                                                                                                                                                                    if __name__ == '__main__':
                                                                                                                                                                        atexit.register(cleanup,)
                                                                                                                                                                        raise SystemExit(main(),)
                                                                                                                                                                        '''

                                                                                                                                                                        def write_file(path: Path,
                                                                                                                                                                            content: str,
                                                                                                                                                                            mode_exec: bool = False) -> None:
                                                                                                                                                                            """TODO: Add docstring."""
                                                                                                                                                                            path.parent.mkdir(parents = True,
                                                                                                                                                                                exist_ok = True)
                                                                                                                                                                            path.write_text(content,
                                                                                                                                                                                encoding = 'utf - 8')
                                                                                                                                                                            if mode_exec:
                                                                                                                                                                                os.chmod(path,
                                                                                                                                                                                    os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,)

                                                                                                                                                                                def ensure_minimal_logger():
                                                                                                                                                                                    """TODO: Add docstring."""
                                                                                                                                                                                    lp = ROOT / 'logger.py'
                                                                                                                                                                                    if not lp.exists():
                                                                                                                                                                                        write_file(lp,
                                                                                                                                                                                            MINIMAL_LOGGER,
                                                                                                                                                                                            mode_exec = False)
                                                                                                                                                                                        print('[ok] created minimal logger.py',)

                                                                                                                                                                                        def ensure_tools_package():
                                                                                                                                                                                            """TODO: Add docstring."""
                                                                                                                                                                                            initp = ROOT / 'tools' / '__init__.py'
                                                                                                                                                                                            if not initp.exists():
                                                                                                                                                                                                write_file(initp,
                                                                                                                                                                                                    "# tools package marker\n")
                                                                                                                                                                                                print('[ok] created tools / __init__.py',)

                                                                                                                                                                                                def write_start_py():
                                                                                                                                                                                                    """TODO: Add docstring."""
                                                                                                                                                                                                    sp = ROOT / 'start.py'
                                                                                                                                                                                                    write_file(sp,
                                                                                                                                                                                                        START_PY,
                                                                                                                                                                                                        mode_exec = True)
                                                                                                                                                                                                    print('[ok] wrote start.py and made it executable',)

                                                                                                                                                                                                    def main():
                                                                                                                                                                                                        """TODO: Add docstring."""
                                                                                                                                                                                                        ensure_minimal_logger(,)
                                                                                                                                                                                                        ensure_tools_package(,)
                                                                                                                                                                                                        write_start_py(,)
                                                                                                                                                                                                        print("\nNext steps: ",)
                                                                                                                                                                                                        print("  1) Run the app:   ./start.py    (or: python3 start.py)",)
                                                                                                                                                                                                        print("  2) Optional envs: START_NO_SCAN = 1,
                                                                                                                                                                                                            START_SCAN_DRY_RUN = 1,
                                                                                                                                                                                                            START_NO_BACKUP = 1,
                                                                                                                                                                                                            START_SCAN_PATH=/path")
                                                                                                                                                                                                        print("  3) To pass args to poker_go.py,
                                                                                                                                                                                                            use:  ./start.py -- --your --poker - go - args")

                                                                                                                                                                                                        if __name__ == '__main__':
                                                                                                                                                                                                            main(,)
