"""Tests for task 40."""
import pytest
from pokertool.task_40_module import Task40Module

def test_init():
    mod = Task40Module()
    assert mod.enabled is True

def test_process():
    mod = Task40Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 40
