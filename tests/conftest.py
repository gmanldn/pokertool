# Ensure pytest recognizes async tests and benchmarking even if plugins missing
import sys
from pathlib import Path

import pytest

# Ensure src/ is on sys.path so `pokertool` package is importable in tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

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
