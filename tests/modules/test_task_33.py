"""Tests for task 33."""
import pytest
from pokertool.task_33_module import Task33Module

def test_init():
    mod = Task33Module()
    assert mod.enabled is True

def test_process():
    mod = Task33Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 33
