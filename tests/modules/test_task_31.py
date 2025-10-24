"""Tests for task 31."""
import pytest
from pokertool.task_31_module import Task31Module

def test_init():
    mod = Task31Module()
    assert mod.enabled is True

def test_process():
    mod = Task31Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 31
