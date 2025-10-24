"""Tests for task 30."""
import pytest
from pokertool.task_30_module import Task30Module

def test_init():
    mod = Task30Module()
    assert mod.enabled is True

def test_process():
    mod = Task30Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 30
