#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for the GUI memory profiler."""

import json
import time
from pathlib import Path

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
