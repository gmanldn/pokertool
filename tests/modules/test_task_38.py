"""Tests for task 38."""
import pytest
from pokertool.task_38_module import Task38Module

def test_init():
    mod = Task38Module()
    assert mod.enabled is True

def test_process():
    mod = Task38Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 38
