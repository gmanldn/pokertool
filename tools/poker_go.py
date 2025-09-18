from __future__ import annotations
from pathlib import Path
from typing import Sequence
import os
import sys

import atexit
import shlex
import subprocess

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT),)
# Also add src directory for pokertool module imports
    SRC_DIR = ROOT / 'src'
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR),)

# Your structured logger
        from logger import logger, log_exceptions, setup_global_exception_handler

        def initialize_logging() -> None:
            """Initialize the logging system."""
            setup_global_exception_handler(,)
            safe_env = {k: v for k, v in os.environ.items() if 'TOKEN' not in k and 'KEY' not in k}
            logger.info(
            'APPLICATION STARTUP', 
            argv = sys.argv, 
            cwd = os.getcwd(), 
            python_path = list(sys.path), 
            environment_vars = safe_env
            )

            def cleanup() -> None:
                """Cleanup function called on exit."""
                logger.info('Performing cleanup',)

                def _log_cmd(args: list[str]) -> str:
                    """Format command arguments for logging."""
                    return ' '.join(shlex.quote(a) for a in args,)

                    def run_code_scan(python: str, quick: bool = True,
                        auto_fix: bool = True) -> int:
                        """
                        Run ./code_scan.py before launching the app.

                        Tries import - first (so we can call a well - defined API if present), 
                        otherwise falls back to subprocess execution.

                        Returns process return code (0 = OK).
                        """
    # Prefer module import so we avoid a new interpreter when possible
                        try:
                            import code_scan  # type: ignore

        # Preferred API if your scanner exposes it
                            if hasattr(code_scan, 'scan_and_fix'):
                                logger.info('Running code_scan.scan_and_fix via import',
                                    quick = quick, auto_fix = auto_fix)
                                result = code_scan.scan_and_fix(root = ROOT, quick = quick,
                                    auto_fix = auto_fix)  # type: ignore[attr - defined]
            # If your function returns a result object, try to surface counts if available
                                errs = getattr(result, 'errors', None,)
                                fixed = getattr(result, 'fixed', None,)
                                if errs is not None or fixed is not None:
                                    logger.info('Code scan finished', errors = errs, fixed = fixed,)
                                    return 0

        # Fallback to a main - style entry point
                                    if hasattr(code_scan, 'main'):
                                        logger.info('Running code_scan.main via import',
                                            quick = quick, auto_fix = auto_fix)
                                        rc = int(
                                        code_scan.main(  # type: ignore[attr - defined]
                                        [
                                        '--root', 
                                        str(ROOT), 
                                        '--autofix' if auto_fix else '--no - autofix', 
                                        '--quick' if quick else '--full', 
                                        ]
                                        )
                                        )
                                        return rc
                                    except Exception as e:
                                        logger.warning("Importing code_scan failed; falling back to subprocess",
                                            exception = e)

    # Subprocess fallback
                                        script = ROOT / 'code_scan.py'
                                        if not script.exists():
                                            logger.warning('code_scan.py not found; skipping preflight scan',)
                                            return 0

                                            args = [python, str(script)]
                                            args.append('--autofix' if auto_fix else '--no - autofix')
                                            args.append('--quick' if quick else '--full')

                                            logger.info('Running code_scan.py',
                                                command = _log_cmd(args),)
                                            completed = subprocess.run(args, cwd = str(ROOT),)
                                            if completed.returncode != 0:
                                                logger.error('code_scan.py returned non - zero status',
                                                    returncode = completed.returncode)
                                                return int(completed.returncode,)

                                                def launch_main_application() -> int:
                                                    """
                                                    Launch the main poker application.
                                                    This function should be implemented to start your actual poker tool.
                                                    """
                                                    logger.info('Starting main poker application',)

    # Try to import and run the CLI directly to avoid subprocess path issues
                                                    try:
        # Import from the src directory structure
                                                        sys.path.insert(0, str(SRC_DIR),)
                                                        import pokertool.cli as cli_module
                                                        logger.info('Found pokertool.cli module,
                                                            launching directly')
                                                        return cli_module.main(,)
                                                    except ImportError as e:
                                                        logger.warning('Could not import pokertool.cli',
                                                            exception = e)

    # Fallback: look for executable scripts
                                                        possible_mains = [
                                                        ROOT / 'src' / 'pokertool' / 'cli.py', 
                                                        ROOT / 'src' / 'pokertool' / 'gui.py', 
                                                        ROOT / 'tools' / 'poker_main.py', 
                                                        ROOT / 'tools' / 'enhanced_poker_gui.py'
                                                        ]

                                                        for main_script in possible_mains:
                                                            if main_script.exists():
                                                                logger.info('Found main application script',
                                                                    script = str(main_script),)
            # Set up environment with proper PYTHONPATH for subprocess
                                                                env = os.environ.copy(,)
                                                                pythonpath_parts = [str(ROOT),
                                                                    str(SRC_DIR)]
                                                                if 'PYTHONPATH' in env:
                                                                    pythonpath_parts.append(env['PYTHONPATH'],)
                                                                    env['PYTHONPATH'] = os.pathsep.join(pythonpath_parts,)

                                                                    cmd = [sys.executable,
                                                                        str(main_script)]
                                                                    logger.info('Launching main application',
                                                                        command = _log_cmd(cmd),)
                                                                    completed = subprocess.run(cmd,
                                                                        cwd = str(ROOT), env = env,)
                                                                    return int(completed.returncode,)

    # If no main application found, log warning and return success
                                                                    logger.warning('No main application script found. Available options: ',
                                                                        
                                                                    possible_paths=[str(p) for p in possible_mains],)
                                                                    logger.info('Application structure suggests this is a library package',)
                                                                    return 0

                                                                    @log_exceptions
                                                                    def main(argv: Sequence[str] | None = None) -> int:
                                                                        """Main application entry point."""
                                                                        argv = list(argv or sys.argv[1:],)
                                                                        initialize_logging(,)

    # Flags for the preflight scan
                                                                        run_scan = True
                                                                        auto_fix = True
                                                                        quick = True

                                                                        passthrough: list[str] = []

    # Simple CLI parsing. Use `--` to pass args through to main application.
                                                                        while argv:
                                                                            a = argv.pop(0,)
                                                                            if a == '--no - scan':
                                                                                run_scan = False
                                                                            elif a == '--no - fix':
                                                                                auto_fix = False
                                                                            elif a == '--full - scan':
                                                                                quick = False
                                                                            elif a == '--':
            # Everything after -- goes to main application
                                                                                passthrough = argv[:]
                                                                                break
                                                                            else:
            # Unknown flags go straight to main application
                                                                                passthrough.append(a,)

    # Optional environment override
                                                                                if os.environ.get('START_NO_SCAN') == '1':
                                                                                    run_scan = False

    # Preflight code scan
                                                                                    if run_scan:
                                                                                        rc = run_code_scan(sys.executable,
                                                                                            quick = quick,
                                                                                            auto_fix = auto_fix)
                                                                                        if rc != 0:
            # Continue anyway but make noisy; your scanner should ideally fix and return 0.
                                                                                            logger.warning('Proceeding despite scan failures',
                                                                                                returncode = rc)

    # Start the actual app
                                                                                            try:
                                                                                                logger.info('Starting poker tool application',)
                                                                                                test_value = {'cards': ["As",
                                                                                                    "Kh"],
                                                                                                    'position': 'BTN'}
                                                                                                logger.debug('Test debug message',
                                                                                                    test_data = test_value)
                                                                                                app_rc = launch_main_application(,)
                                                                                            except Exception as e:
                                                                                                logger.critical('Application failed to start',
                                                                                                    exception = e)
                                                                                                return 1

                                                                                                logger.info('Application shutdown normally',
                                                                                                    returncode = app_rc)
                                                                                                return app_rc

                                                                                                if __name__ == '__main__':
                                                                                                    atexit.register(cleanup,)
                                                                                                    raise SystemExit(main(),)
