"""Tests for task 34."""
import pytest
from pokertool.task_34_module import Task34Module

def test_init():
    mod = Task34Module()
    assert mod.enabled is True

def test_process():
    mod = Task34Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 34
