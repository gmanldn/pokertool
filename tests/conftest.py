# Ensure pytest recognizes async tests and benchmarking even if plugins missing
import pytest

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