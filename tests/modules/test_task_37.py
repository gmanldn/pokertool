"""Tests for task 37."""
import pytest
from pokertool.task_37_module import Task37Module

def test_init():
    mod = Task37Module()
    assert mod.enabled is True

def test_process():
    mod = Task37Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 37
