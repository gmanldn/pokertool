#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore

from pokertool.api import FASTAPI_AVAILABLE, create_app, get_api


pytestmark = pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI dependencies not available")


def _admin_token() -> str:
    # Create a fresh admin token directly via the API auth service
    api = get_api()
    admin_user = api.services.auth_service.users['admin']
    return api.services.auth_service.create_access_token(admin_user)


def _user_token() -> str:
    api = get_api()
    user = api.services.auth_service.users['demo_user']
    return api.services.auth_service.create_access_token(user)


@pytest.mark.api
def test_admin_endpoints_enforce_admin_role():
    app = create_app()
    client = TestClient(app)

    # Non-admin token (demo_user)
    user_token = _user_token()

    # Admin-only endpoints should reject non-admin
    r = client.get("/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403

    r = client.get("/admin/system/stats", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403

    # Admin token
    admin_token = _admin_token()

    r = client.get("/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, dict) and isinstance(body.get('users'), list)

    r = client.get("/admin/system/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert "websockets" in r.json()
