#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time

import pytest

try:
    from starlette.testclient import TestClient
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore

from pokertool.api import FASTAPI_AVAILABLE, create_app


pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI dependencies not available")


def _next_ws_json(ws):
    """Helper: receive next JSON message with a small safety timeout."""
    # starlette TestClient websockets block until a message arrives; we rely on
    # app background task scheduling to deliver within a reasonable time.
    return ws.receive_json()


@pytest.mark.api
def test_system_health_websocket_connect_ping_refresh_and_reconnect():
    """
    Verifies the system-health WebSocket end-to-end:
    - Connect receives welcome + initial health snapshot
    - ping -> pong
    - POST refresh triggers broadcast 'health_update'
    - Disconnect and reconnect still yields expected messages
    """
    app = create_app()
    client = TestClient(app)

    with client.websocket_connect("/ws/system-health") as ws:
        # 1) Welcome message
        msg = _next_ws_json(ws)
        assert msg["type"] == "system"
        assert "Connected to system health monitor" in msg.get("message", "")

        # 2) Initial health snapshot (may be 'unknown' on first connect)
        msg = _next_ws_json(ws)
        assert msg["type"] == "health_update"
        assert "timestamp" in msg
        assert "data" in msg

        # 3) ping -> pong
        ws.send_text("ping")
        msg = _next_ws_json(ws)
        assert msg["type"] == "pong"

        # 4) Request a refresh via WebSocket and expect a fresh health_update
        ws.send_text("refresh")
        msg = _next_ws_json(ws)
        assert msg["type"] == "health_update"
        assert "data" in msg

    # 5) Reconnect quickly and ensure we still get welcome + snapshot
    with client.websocket_connect("/ws/system-health") as ws:
        msg = _next_ws_json(ws)
        assert msg["type"] == "system"
        msg = _next_ws_json(ws)
        assert msg["type"] == "health_update"
