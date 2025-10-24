"""Tests for task 32."""
import pytest
from pokertool.task_32_module import Task32Module

def test_init():
    mod = Task32Module()
    assert mod.enabled is True

def test_process():
    mod = Task32Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 32
