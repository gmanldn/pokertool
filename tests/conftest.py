# Ensure pytest recognizes async tests and benchmarking even if plugins missing
import sys
import os
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
