# Ensure pytest recognizes async tests and benchmarking even if plugins missing
import os
import sys
import time
from pathlib import Path

import pytest

# Ensure src/ is on sys.path so `pokertool` package is importable in tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

# Ensure both the project root (for `import src.*`) and the src folder
# (for `import pokertool`) are importable during tests.
for path in (PROJECT_ROOT, SRC_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Set test mode to suppress GUI popups during testing
os.environ['POKERTOOL_TEST_MODE'] = '1'

# Provide a compatibility shim for pytesseract when OpenCV arrays are used.
try:  # pragma: no cover - optional dependency
    import pytesseract  # type: ignore
    import numpy as np
    from PIL import Image

    _orig_image_to_string = pytesseract.image_to_string

    def _image_to_string_compat(image, *args, **kwargs):
        if hasattr(image, "shape") and hasattr(image, "dtype"):
            pil_image = Image.fromarray(np.asarray(image))
            if pil_image.mode not in {"L", "RGB"}:
                pil_image = pil_image.convert("RGB")
            image = pil_image
        return _orig_image_to_string(image, *args, **kwargs)

    pytesseract.image_to_string = _image_to_string_compat
except Exception:
    pass

# Register pytest-asyncio automatically if available
pytest_plugins = []
try:
    import pytest_asyncio  # noqa: F401
    pytest_plugins.append("pytest_asyncio")
except ImportError:
    pass

# Provide a dummy benchmark fixture if pytest-benchmark is not installed
@pytest.fixture
def benchmark(request):
    try:
        import pytest_benchmark.plugin  # noqa: F401
    except ImportError:
        # Fallback: simple passthrough benchmark
        def _benchmark(func, *args, **kwargs):
            return func(*args, **kwargs)
        return _benchmark
    # Otherwise defer to real plugin
    return request.getfixturevalue("benchmark")


# ============================================================================
# Architecture Graph Database Integration
# ============================================================================

def pytest_addoption(parser):
    """Add custom command-line options"""
    parser.addoption(
        "--update-graph",
        action="store_true",
        default=False,
        help="Rebuild the architecture graph before running tests"
    )
    parser.addoption(
        "--no-live-progress",
        action="store_true",
        default=False,
        help="Disable live start/completion streaming for tests"
    )


def pytest_configure(config):
    """Configure pytest with custom markers and hooks"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

    # If --update-graph flag is set, rebuild the graph before running tests
    if config.getoption("--update-graph"):
        print("\n" + "=" * 70)
        print("Rebuilding architecture graph...")
        print("=" * 70 + "\n")

        # Import and run the graph builder
        arch_dir = Path(__file__).parent / 'architecture'
        sys.path.insert(0, str(arch_dir))
        try:
            from graph_builder import ArchitectureGraphBuilder

            source_root = Path.cwd()
            data_dir = arch_dir / 'data'

            builder = ArchitectureGraphBuilder(source_root, data_dir)
            builder.build()

            print("\n" + "=" * 70)
            print("Graph rebuild complete. Starting tests...")
            print("=" * 70 + "\n")

        except Exception as e:
            print(f"\n❌ Error rebuilding graph: {e}")
            print("Continuing with existing graph...\n")

    if config.getoption("no_live_progress"):
        _LIVE_PROGRESS.disable()
    else:
        _LIVE_PROGRESS.configure(config)


@pytest.fixture(scope="session")
def graph_store():
    """
    Session-scoped fixture providing access to the architecture graph.

    This fixture is shared across all tests in the session to avoid
    reloading the graph multiple times.
    """
    arch_dir = Path(__file__).parent / 'architecture'
    sys.path.insert(0, str(arch_dir))
    from storage.json_store import ArchitectureGraphStore

    data_dir = arch_dir / 'data'
    store = ArchitectureGraphStore(data_dir)

    if not store.load():
        pytest.fail(
            "Failed to load architecture graph. "
            "Run with --update-graph to rebuild it."
        )

    return store


@pytest.fixture(scope="session")
def graph_builder():
    """
    Session-scoped fixture providing access to the graph builder.

    Useful for tests that need to rebuild specific parts of the graph.
    """
    arch_dir = Path(__file__).parent / 'architecture'
    sys.path.insert(0, str(arch_dir))
    from graph_builder import ArchitectureGraphBuilder

    source_root = Path.cwd()
    data_dir = arch_dir / 'data'

    return ArchitectureGraphBuilder(source_root, data_dir)


_SKIP_TEST_MODE_FILES = {
    "test_betfair_fixed.py",
    "test_bf_detection.py",
}


def pytest_ignore_collect(path, config):  # pragma: no cover - collection hook
    """Skip heavy integration scripts when test mode is enabled."""
    if os.environ.get("POKERTOOL_TEST_MODE") != "1":
        return None

    try:
        filename = path.name
    except AttributeError:
        filename = path.basename  # type: ignore[attr-defined]

    if filename in _SKIP_TEST_MODE_FILES:
        return True
    return None


class _LiveProgressPlugin:
    """Emit real-time test lifecycle feedback to the terminal."""

    _STATUS_LABELS = {
        "passed": "PASS",
        "failed": "FAIL",
        "skipped": "SKIP",
    }

    def __init__(self):
        self._terminal_reporter = None
        self._start_times = {}
        self._enabled = False
        self._total = 0
        self._running = set()
        self._node_outcomes = {}
        self._passed = 0
        self._failed = 0
        self._skipped = 0

    def configure(self, config):
        self._terminal_reporter = config.pluginmanager.getplugin("terminalreporter")
        self._reset_stats()
        self._enabled = True

    def disable(self):
        self._enabled = False
        self._reset_stats()

    def session_start(self):
        self._reset_stats()

    def collection_finished(self, session):
        if not self._enabled:
            return
        self._total = len(session.items)
        self._write_line(f"[ INFO  ] Collected {self._total} tests")

    def _reset_stats(self):
        self._start_times.clear()
        self._running.clear()
        self._node_outcomes.clear()
        self._passed = 0
        self._failed = 0
        self._skipped = 0
        self._total = 0

    def _remaining(self):
        if self._total <= 0:
            return "?"
        remaining = self._total - len(self._node_outcomes)
        return max(remaining, 0)

    def _write_line(self, message, color=None, bold=False):
        if not self._enabled:
            return
        if self._terminal_reporter is not None:
            self._terminal_reporter.ensure_newline()
            kwargs = {}
            if color in {"green", "red", "yellow", "blue", "magenta", "cyan"}:
                kwargs[color] = True
            if bold:
                kwargs["bold"] = True
            self._terminal_reporter.write_line(message, **kwargs)
        else:
            print(message, flush=True)

    def log_start(self, nodeid, location):
        if not self._enabled:
            return
        self._start_times[nodeid] = time.perf_counter()
        self._running.add(nodeid)
        line = self._format_counts(f"[ START ] {nodeid}")
        self._write_line(line)

    def log_report(self, report):
        if not self._enabled:
            return
        nodeid = report.nodeid
        when = report.when
        outcome = report.outcome

        if when == "setup" and outcome in {"failed", "skipped"}:
            self._emit_terminal_status(nodeid, outcome, report, stage=when)
        elif when == "call":
            status = outcome
            if getattr(report, "wasxfail", False):
                status = "xpass" if outcome == "passed" else "xfail"
            self._emit_terminal_status(nodeid, status, report)
        elif when == "teardown" and outcome == "failed":
            self._emit_terminal_status(nodeid, outcome, report, stage=when)

    def _emit_terminal_status(self, nodeid, outcome, report, stage=None):
        status = self._STATUS_LABELS.get(outcome, outcome.upper())
        if stage and stage not in {"call"}:
            status = f"{status}-{stage.upper()}"

        duration = None
        started_at = self._start_times.pop(nodeid, None)
        if started_at is not None:
            duration = time.perf_counter() - started_at
        elif hasattr(report, "duration"):
            duration = report.duration

        final_status = self._classify_final_status(outcome, report)
        self._update_outcome_stats(nodeid, final_status)
        self._running.discard(nodeid)

        line = f"[ {status:>7} ] {nodeid}"
        if duration is not None:
            line += f" ({duration:0.2f}s)"

        if outcome in {"skipped", "xfail"} and hasattr(report, "longrepr"):
            reason = self._extract_skip_reason(report.longrepr)
            if reason:
                line += f" - {reason}"

        line = self._format_counts(line)
        self._write_line(line, color=self._status_to_color(final_status), bold=(final_status == "passed"))

    @staticmethod
    def _extract_skip_reason(longrepr):
        if isinstance(longrepr, tuple) and len(longrepr) >= 3:
            return str(longrepr[2]).strip()
        if hasattr(longrepr, "message"):
            return str(longrepr.message).strip()
        if hasattr(longrepr, "strerror"):
            return str(longrepr.strerror).strip()
        return None

    def _classify_final_status(self, outcome, report):
        if getattr(report, "wasxfail", False):
            if outcome == "passed":
                return "xpassed"
            return "xfailed"

        if outcome == "passed":
            return "passed"
        if outcome == "failed":
            return "failed"
        if outcome == "skipped":
            return "skipped"
        return outcome

    def _update_outcome_stats(self, nodeid, status):
        previous = self._node_outcomes.get(nodeid)
        if previous == status:
            return
        if previous is not None:
            self._apply_status_delta(previous, -1)
        self._node_outcomes[nodeid] = status
        self._apply_status_delta(status, 1)

    def _apply_status_delta(self, status, delta):
        if status == "passed":
            self._passed += delta
        elif status in {"failed", "xpassed"}:
            self._failed += delta
        elif status in {"skipped", "xfailed"}:
            self._skipped += delta

    def _format_counts(self, line):
        remaining = self._remaining()
        return f"{line} | pass={self._passed} fail={self._failed} left={remaining}"

    @staticmethod
    def _status_to_color(status):
        if status == "passed":
            return "green"
        if status in {"failed", "xpassed"}:
            return "red"
        if status in {"skipped", "xfailed"}:
            return "yellow"
        return None


_LIVE_PROGRESS = _LiveProgressPlugin()


def pytest_runtest_logstart(nodeid, location):  # pragma: no cover - integration hook
    _LIVE_PROGRESS.log_start(nodeid, location)


def pytest_runtest_logreport(report):  # pragma: no cover - integration hook
    _LIVE_PROGRESS.log_report(report)


def pytest_report_teststatus(report, config):  # pragma: no cover - integration hook
    if config.getoption("no_live_progress"):
        return None

    when = getattr(report, "when", None)
    if when != "call":
        return None

    category = report.outcome
    if getattr(report, "wasxfail", False):
        category = "xfailed" if report.skipped else "xpassed"

    verbose = category.upper()
    return category, "", verbose


def pytest_sessionstart(session):  # pragma: no cover - integration hook
    if session.config.getoption("no_live_progress"):
        return
    _LIVE_PROGRESS.session_start()


def pytest_collection_finish(session):  # pragma: no cover - integration hook
    if session.config.getoption("no_live_progress"):
        return
    _LIVE_PROGRESS.collection_finished(session)
