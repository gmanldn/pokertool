"""Tests for task 46."""
import pytest
from pokertool.task_46_module import Task46Module

def test_init():
    mod = Task46Module()
    assert mod.enabled is True

def test_process():
    mod = Task46Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 46
