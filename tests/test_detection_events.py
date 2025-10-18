# -*- coding: utf-8 -*-

import asyncio
import importlib
import sys
import threading
import types
from typing import List, Tuple

import pytest


@pytest.fixture(autouse=True)
def _reload_detection_events(monkeypatch):
    """
    Reload detection_events module for each test to ensure a clean state and
    provide a lightweight stub for pokertool.api.broadcast_detection_event.
    """
    calls: List[Tuple[str, str, str, dict]] = []

    async def fake_broadcast_detection_event(event_type, severity, message, data=None):
        calls.append((event_type, severity, message, data or {}))

    stub_api = types.SimpleNamespace(broadcast_detection_event=fake_broadcast_detection_event)
    monkeypatch.setitem(sys.modules, 'pokertool.api', stub_api)

    detection_events = importlib.reload(importlib.import_module('pokertool.detection_events'))
    detection_events.clear_detection_event_loop()

    yield detection_events, calls

    detection_events.clear_detection_event_loop()


def test_emit_detection_event_dispatches_immediately(_reload_detection_events):
    detection_events, calls = _reload_detection_events

    async def runner():
        detection_events.register_detection_event_loop(asyncio.get_running_loop())
        detection_events.emit_detection_event(
            event_type='system',
            severity='info',
            message='Immediate dispatch',
            data={'key': 'value'},
        )
        await asyncio.sleep(0)

    asyncio.run(runner())

    assert calls == [
        ('system', 'info', 'Immediate dispatch', {'key': 'value'}),
    ]


def test_emit_detection_event_buffers_without_loop(_reload_detection_events):
    detection_events, calls = _reload_detection_events

    def emit_from_thread():
        detection_events.emit_detection_event(
            event_type='system',
            severity='warning',
            message='Buffered dispatch',
            data={'source': 'thread'},
        )

    worker = threading.Thread(target=emit_from_thread)
    worker.start()
    worker.join()

    # No loop registered yet, so nothing should have been broadcast
    assert calls == []

    async def runner():
        detection_events.register_detection_event_loop(asyncio.get_running_loop())
        await asyncio.sleep(0)

    asyncio.run(runner())

    assert calls == [
        ('system', 'warning', 'Buffered dispatch', {'source': 'thread'}),
    ]
