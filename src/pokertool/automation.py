"""Developer automation helpers for PokerTool."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import subprocess
import sys
import time
from hashlib import sha256
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT_DIR / 'state' / 'ml-tests'
SENTINEL_PATH = STATE_DIR / 'last-success.json'
REQUIREMENTS_FILE = ROOT_DIR / 'requirements.txt'
# Torch is handled as an optional accelerator; keep ML automation focused on CPU-friendly deps.
REQUIRED_MODULES = (
    'tensorflow',
    'pandas',
    'sklearn',
)
TEST_TARGETS: tuple[str, ...] = ('tests',)


def _hash_file(path: Path) -> str:
    if not path.exists():
        return ''
    digest = sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _get_git_head() -> str:
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT_DIR,
        )
        return result.stdout.strip()
    except Exception:
        return 'unknown'


def _missing_modules(modules: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for module in modules:
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing


def ensure_ml_tests_run(logger=None) -> None:
    """Run the full pytest suite once the heavyweight ML dependencies are present."""
    # Handle both standard logging.Logger and custom MasterLogger
    if logger is None:
        log = logging.getLogger(__name__)
    elif hasattr(logger, 'info') and callable(getattr(logger, 'info')):
        log = logger  # Use the custom logger directly
    else:
        log = logging.getLogger(__name__)

    if os.environ.get('POKERTOOL_SKIP_AUTO_TESTS') == '1':
        log.info('Skipping ML auto-tests due to POKERTOOL_SKIP_AUTO_TESTS=1')
        return

    missing = _missing_modules(REQUIRED_MODULES)
    if missing:
        log.info('Skipping ML auto-tests; dependencies missing', missing=missing)
        return

    if importlib.util.find_spec('pytest') is None:
        log.info('Skipping ML auto-tests; pytest is not installed')
        return

    requirements_hash = _hash_file(REQUIREMENTS_FILE)
    identity = {
        'requirements_hash': requirements_hash,
        'git_head': _get_git_head(),
    }

    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        if hasattr(log, 'warning') and hasattr(log, 'error'):
            # Custom MasterLogger with exception parameter
            try:
                log.warning('Unable to prepare state directory for ML auto-tests', exception=exc)
            except TypeError:
                # Fallback to standard logging format
                log.warning('Unable to prepare state directory for ML auto-tests: %s', str(exc))
        else:
            log.warning('Unable to prepare state directory for ML auto-tests: %s', str(exc))
        return

    if SENTINEL_PATH.exists():
        try:
            previous = json.loads(SENTINEL_PATH.read_text())
        except Exception:
            previous = {}
        if (
            previous.get('requirements_hash') == identity['requirements_hash']
            and previous.get('git_head') == identity['git_head']
        ):
            log.debug('ML auto-tests already ran for current environment; skipping')
            return

    log.info('Running ML test suite automatically', targets=TEST_TARGETS)
    env = os.environ.copy()
    env['POKERTOOL_SKIP_AUTO_TESTS'] = '1'

    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', *TEST_TARGETS],
            cwd=ROOT_DIR,
            env=env,
            check=False,
        )
    except Exception as exc:
        if hasattr(log, 'error') and hasattr(log, 'warning'):
            # Custom MasterLogger with exception parameter
            try:
                log.error('Failed to execute pytest for ML auto-tests', exception=exc)
            except TypeError:
                # Fallback to standard logging format
                log.error('Failed to execute pytest for ML auto-tests: %s', str(exc))
        else:
            log.error('Failed to execute pytest for ML auto-tests: %s', str(exc))
        return

    if result.returncode != 0:
        log.error('ML auto-tests failed', returncode=result.returncode)
        return

    identity['timestamp'] = time.time()
    try:
        SENTINEL_PATH.write_text(json.dumps(identity, indent=2))
    except Exception as exc:
        if hasattr(log, 'warning') and hasattr(log, 'error'):
            # Custom MasterLogger with exception parameter
            try:
                log.warning('Failed to persist ML auto-test sentinel; tests may rerun', exception=exc)
            except TypeError:
                # Fallback to standard logging format
                log.warning('Failed to persist ML auto-test sentinel; tests may rerun: %s', str(exc))
        else:
            log.warning('Failed to persist ML auto-test sentinel; tests may rerun: %s', str(exc))
        return

    log.info('ML auto-tests completed successfully')
