"""Tests for task 44."""
import pytest
from pokertool.task_44_module import Task44Module

def test_init():
    mod = Task44Module()
    assert mod.enabled is True

def test_process():
    mod = Task44Module()
    result = mod.process()
    assert result["status"] == "ok"
    assert result["task"] == 44
