"""Tests for task 48."""
import pytest
from pokertool.task_48_module import Task48Module

def test_init():
    mod = Task48Module()
    assert mod.enabled is True

def test_process():
    mod = Task48Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 48
