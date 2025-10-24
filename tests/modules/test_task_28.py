"""Tests for task 28."""
import pytest
from pokertool.task_28_module import Task28Module

def test_init():
    mod = Task28Module()
    assert mod.enabled is True

def test_process():
    mod = Task28Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 28
