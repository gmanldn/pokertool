"""Tests for task 36."""
import pytest
from pokertool.task_36_module import Task36Module

def test_init():
    mod = Task36Module()
    assert mod.enabled is True

def test_process():
    mod = Task36Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 36
