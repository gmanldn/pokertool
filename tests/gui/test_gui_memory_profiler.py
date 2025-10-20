#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for the GUI memory profiler."""

import json
import time
import threading
from pathlib import Path
from typing import List

from pokertool.gui_memory_profiler import GuiMemoryProfiler


def test_gui_memory_profiler_writes_samples(tmp_path: Path):
    """Profiler should produce JSONL samples after running."""
    profiler = GuiMemoryProfiler(sample_interval=0.01, report_limit=3, output_dir=tmp_path)
    profiler.start()
    time.sleep(0.05)
    profiler.stop()

    output_files = list(tmp_path.glob('gui_memory.jsonl'))
    assert output_files, "Expected profiler output file"

    lines = output_files[0].read_text(encoding='utf-8').strip().splitlines()
    assert lines, "Profiler should write at least one sample"

    sample = json.loads(lines[-1])
    assert 'timestamp' in sample
    assert 'current_kb' in sample
    assert 'top_allocations' in sample


def test_profiler_tracks_thread_count(tmp_path: Path):
    """Profiler should track active thread counts."""
    profiler = GuiMemoryProfiler(sample_interval=0.02, output_dir=tmp_path)
    profiler.start()

    # Create additional threads to simulate thread leaks
    threads: List[threading.Thread] = []
    stop_events: List[threading.Event] = []

    def worker(stop_event: threading.Event):
        """Simple worker thread."""
        while not stop_event.wait(0.01):
            pass

    # Start some threads
    for i in range(3):
        stop_event = threading.Event()
        t = threading.Thread(target=worker, args=(stop_event,), daemon=True)
        t.start()
        threads.append(t)
        stop_events.append(stop_event)

    time.sleep(0.06)  # Wait for samples

    # Stop threads
    for stop_event in stop_events:
        stop_event.set()
    for t in threads:
        t.join(timeout=1)

    profiler.stop()

    # Verify samples captured thread count
    output_file = tmp_path / 'gui_memory.jsonl'
    lines = output_file.read_text(encoding='utf-8').strip().splitlines()
    assert len(lines) >= 2, "Should have captured multiple samples"

    samples = [json.loads(line) for line in lines]
    for sample in samples:
        assert 'thread_count' in sample
        assert sample['thread_count'] > 0


def test_profiler_detects_memory_growth(tmp_path: Path):
    """Profiler should track memory growth patterns."""
    profiler = GuiMemoryProfiler(sample_interval=0.02, output_dir=tmp_path)
    profiler.start()

    # Simulate memory allocation (potential leak)
    allocations: List[List[int]] = []

    # First sample
    time.sleep(0.025)

    # Allocate memory
    for _ in range(100):
        allocations.append([i for i in range(1000)])

    # Second sample
    time.sleep(0.025)

    # Allocate more memory
    for _ in range(100):
        allocations.append([i for i in range(1000)])

    # Third sample
    time.sleep(0.025)

    profiler.stop()

    # Verify samples show memory growth
    output_file = tmp_path / 'gui_memory.jsonl'
    lines = output_file.read_text(encoding='utf-8').strip().splitlines()
    assert len(lines) >= 2, "Should have multiple samples"

    samples = [json.loads(line) for line in lines]

    # Verify memory increased over time
    current_mems = [s['current_kb'] for s in samples]
    assert len(current_mems) >= 2
    # At least one sample should show higher memory than the first
    assert max(current_mems) > current_mems[0], "Memory should grow with allocations"


def test_profiler_tracks_allocation_sources(tmp_path: Path):
    """Profiler should identify top allocation sources."""
    profiler = GuiMemoryProfiler(sample_interval=0.02, report_limit=5, output_dir=tmp_path)
    profiler.start()

    # Allocate memory from this test
    test_allocations = [bytearray(10000) for _ in range(10)]  # noqa: F841

    time.sleep(0.05)
    profiler.stop()

    # Verify allocations are tracked
    output_file = tmp_path / 'gui_memory.jsonl'
    lines = output_file.read_text(encoding='utf-8').strip().splitlines()
    assert lines, "Should have samples"

    sample = json.loads(lines[-1])
    assert 'top_allocations' in sample
    assert len(sample['top_allocations']) > 0

    # Each allocation should have location and size
    for alloc in sample['top_allocations']:
        assert 'location' in alloc
        assert 'size_kb' in alloc
        assert 'count' in alloc
        assert 'traceback' in alloc


def test_profiler_context_manager(tmp_path: Path):
    """Profiler should work as context manager."""
    with GuiMemoryProfiler(sample_interval=0.01, output_dir=tmp_path) as profiler:
        time.sleep(0.03)
        assert profiler._started

    # Should be stopped after context exit
    assert not profiler._started

    # Should have written samples
    output_file = tmp_path / 'gui_memory.jsonl'
    assert output_file.exists()
    lines = output_file.read_text(encoding='utf-8').strip().splitlines()
    assert len(lines) >= 1


def test_profiler_handles_restart(tmp_path: Path):
    """Profiler should handle multiple start/stop cycles."""
    profiler = GuiMemoryProfiler(sample_interval=0.01, output_dir=tmp_path)

    # First cycle
    profiler.start()
    time.sleep(0.03)
    profiler.stop()

    output_file = tmp_path / 'gui_memory.jsonl'
    lines1 = output_file.read_text(encoding='utf-8').strip().splitlines()
    count1 = len(lines1)

    # Second cycle
    profiler.start()
    time.sleep(0.03)
    profiler.stop()

    lines2 = output_file.read_text(encoding='utf-8').strip().splitlines()
    count2 = len(lines2)

    # Should have more samples after second run
    assert count2 > count1


def test_profiler_peak_memory_tracking(tmp_path: Path):
    """Profiler should track peak memory usage."""
    profiler = GuiMemoryProfiler(sample_interval=0.02, output_dir=tmp_path)
    profiler.start()

    # Allocate and deallocate to create peak
    temp_allocations = [bytearray(50000) for _ in range(20)]
    time.sleep(0.025)
    del temp_allocations

    time.sleep(0.025)
    profiler.stop()

    # Verify peak memory is tracked
    output_file = tmp_path / 'gui_memory.jsonl'
    lines = output_file.read_text(encoding='utf-8').strip().splitlines()

    samples = [json.loads(line) for line in lines]
    for sample in samples:
        assert 'peak_kb' in sample
        assert sample['peak_kb'] >= sample['current_kb']
