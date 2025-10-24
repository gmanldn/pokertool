"""Tests for task 47."""
import pytest
from pokertool.task_47_module import Task47Module

def test_init():
    mod = Task47Module()
    assert mod.enabled is True

def test_process():
    mod = Task47Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 47
