#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for frontend error monitor."""

import pytest
from pathlib import Path
import tempfile
import shutil

from pokertool.frontend_error_monitor import FrontendErrorMonitor


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def monitor(temp_dir):
    """Create error monitor with temp directories."""
    return FrontendErrorMonitor(log_dir=str(temp_dir / "logs"), root_dir=temp_dir)


def test_detects_module_not_found_error(monitor):
    """Test detection of module not found errors."""
    line = "Module not found: Error: Can't resolve 'some-module'"
    assert monitor.process_line(line) is True
    assert monitor.has_errors() is True

    errors = monitor.get_errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'MODULE_NOT_FOUND'


def test_detects_import_error(monitor):
    """Test detection of import errors."""
    line = "Attempted import error: 'Component' is not exported from './components'"
    assert monitor.process_line(line) is True
    assert monitor.has_errors() is True

    errors = monitor.get_errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'IMPORT_ERROR'


def test_detects_syntax_error(monitor):
    """Test detection of syntax errors."""
    line = "SyntaxError: Unexpected token <"
    assert monitor.process_line(line) is True
    assert monitor.has_errors() is True

    errors = monitor.get_errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'SYNTAX_ERROR'


def test_detects_failed_to_compile(monitor):
    """Test detection of compile failure."""
    line = "Failed to compile."
    assert monitor.process_line(line) is True
    assert monitor.has_errors() is True

    errors = monitor.get_errors()
    assert len(errors) == 1
    assert errors[0]['type'] == 'COMPILATION_FAILED'


def test_ignores_non_error_lines(monitor):
    """Test that normal output is ignored."""
    lines = [
        "Compiled successfully!",
        "webpack compiled with 1 warning",
        "On Your Network:  http://192.168.1.1:3000",
    ]

    for line in lines:
        assert monitor.process_line(line) is False

    assert monitor.has_errors() is False
    assert len(monitor.get_errors()) == 0


def test_writes_to_log_file(monitor, temp_dir):
    """Test that errors are written to log file."""
    monitor.process_line("Module not found: Error: Can't resolve 'test'")
    monitor.process_line("Failed to compile.")

    monitor.write_to_log()

    log_file = temp_dir / "logs" / "frontend_compile_errors.log"
    assert log_file.exists()

    content = log_file.read_text()
    assert "Frontend Compile Errors" in content
    assert "MODULE_NOT_FOUND" in content
    assert "COMPILATION_FAILED" in content


def test_adds_to_todo(monitor, temp_dir):
    """Test that errors are added to TODO.md."""
    # Create mock TODO.md
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    todo_file = docs_dir / "TODO.md"

    todo_content = """# TODO

## Now (P0: highest ROI)

- [ ] Existing task

## Next (P1)

- [ ] Another task
"""
    todo_file.write_text(todo_content)

    # Add some errors
    monitor.process_line("Module not found: Error: Can't resolve 'test-module'")
    monitor.process_line("Failed to compile.")

    # Add to TODO
    monitor.add_to_todo()

    # Verify TODO was updated
    updated_content = todo_file.read_text()
    assert "fix frontend module" in updated_content.lower()
    assert "fix frontend compilation" in updated_content.lower()
    assert "[P0][S]" in updated_content
    assert "logs/frontend_compile_errors.log" in updated_content


def test_multiple_errors_same_type(monitor, temp_dir):
    """Test handling multiple errors of the same type."""
    # Create mock TODO.md
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    todo_file = docs_dir / "TODO.md"
    todo_file.write_text("# TODO\n\n## Now (P0: highest ROI)\n\n")

    # Add multiple MODULE_NOT_FOUND errors
    monitor.process_line("Module not found: Error: Can't resolve 'module-a'")
    monitor.process_line("Module not found: Error: Can't resolve 'module-b'")
    monitor.process_line("Module not found: Error: Can't resolve 'module-c'")

    assert len(monitor.get_errors()) == 3

    monitor.add_to_todo()

    updated_content = todo_file.read_text()
    # Should create one TODO entry with occurrence count
    assert "Total occurrences: 3" in updated_content


def test_thread_safety(monitor):
    """Test thread-safe access to error list."""
    import threading

    def add_errors():
        for i in range(100):
            monitor.process_line(f"Failed to compile. Error {i}")

    threads = [threading.Thread(target=add_errors) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Should have recorded all 500 errors
    assert len(monitor.get_errors()) == 500


def test_shutdown_with_errors(monitor, temp_dir, capsys):
    """Test shutdown_with_errors method."""
    # Create mock TODO.md
    docs_dir = temp_dir / "docs"
    docs_dir.mkdir()
    todo_file = docs_dir / "TODO.md"
    todo_file.write_text("# TODO\n\n## Now (P0: highest ROI)\n\n")

    # Add errors
    monitor.process_line("Module not found: Error: Can't resolve 'test'")
    monitor.process_line("Failed to compile.")

    # Call shutdown
    monitor.shutdown_with_errors()

    # Verify output
    captured = capsys.readouterr()
    assert "FRONTEND COMPILE ERROR DETECTED" in captured.out
    assert "Errors logged to" in captured.out
    assert "Added P0 tasks to docs/TODO.md" in captured.out

    # Verify log file created
    log_file = temp_dir / "logs" / "frontend_compile_errors.log"
    assert log_file.exists()

    # Verify TODO updated
    todo_content = todo_file.read_text()
    assert "[P0][S]" in todo_content
