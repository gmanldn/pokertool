"""Tests for task 35."""
import pytest
from pokertool.task_35_module import Task35Module

def test_init():
    mod = Task35Module()
    assert mod.enabled is True

def test_process():
    mod = Task35Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 35
