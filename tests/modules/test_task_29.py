"""Tests for task 29."""
import pytest
from pokertool.task_29_module import Task29Module

def test_init():
    mod = Task29Module()
    assert mod.enabled is True

def test_process():
    mod = Task29Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 29
