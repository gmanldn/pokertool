"""Tests for task 42."""
import pytest
from pokertool.task_42_module import Task42Module

def test_init():
    mod = Task42Module()
    assert mod.enabled is True

def test_process():
    mod = Task42Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 42
