"""Tests for task 41."""
import pytest
from pokertool.task_41_module import Task41Module

def test_init():
    mod = Task41Module()
    assert mod.enabled is True

def test_process():
    mod = Task41Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 41
