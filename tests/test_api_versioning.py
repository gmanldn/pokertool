#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite for API Versioning
==============================

Comprehensive tests for API version management and middleware.

Module: tests.test_api_versioning
Version: 1.0.0
"""

import pytest
from datetime import date, timedelta
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from pokertool.api_versioning import (
    VersionStatus,
    VersionInfo,
    APIVersionManager,
    APIVersionMiddleware,
    get_version_manager,
    setup_api_versioning
)


class TestVersionInfo:
    """Test VersionInfo dataclass."""

    def test_version_info_creation(self):
        """Test creating version info."""
        info = VersionInfo(
            version="v1",
            status=VersionStatus.STABLE,
            release_date=date(2025, 10, 1),
            description="Initial release"
        )

        assert info.version == "v1"
        assert info.status == VersionStatus.STABLE
        assert info.release_date == date(2025, 10, 1)
        assert info.description == "Initial release"


class TestAPIVersionManager:
    """Test API version manager."""

    def test_register_version(self):
        """Test registering a version."""
        manager = APIVersionManager()

        manager.register_version(
            version="v1",
            status=VersionStatus.STABLE,
            description="Version 1"
        )

        assert "v1" in manager.versions
        assert manager.versions["v1"].status == VersionStatus.STABLE

    def test_first_version_becomes_default(self):
        """Test first registered version becomes default."""
        manager = APIVersionManager()

        manager.register_version("v1", VersionStatus.STABLE)

        assert manager.get_default_version() == "v1"

    def test_set_default_version(self):
        """Test setting default version."""
        manager = APIVersionManager()

        manager.register_version("v1", VersionStatus.STABLE)
        manager.register_version("v2", VersionStatus.STABLE)

        manager.set_default_version("v2")

        assert manager.get_default_version() == "v2"

    def test_set_default_version_unregistered_raises_error(self):
        """Test setting unregistered version as default raises error."""
        manager = APIVersionManager()

        with pytest.raises(ValueError, match="not registered"):
            manager.set_default_version("v999")

    def test_is_version_supported(self):
        """Test checking if version is supported."""
        manager = APIVersionManager()

        manager.register_version("v1", VersionStatus.STABLE)
        manager.register_version("v2", VersionStatus.SUNSET)

        assert manager.is_version_supported("v1") is True
        assert manager.is_version_supported("v2") is False
        assert manager.is_version_supported("v3") is False

    def test_is_version_deprecated(self):
        """Test checking if version is deprecated."""
        manager = APIVersionManager()

        manager.register_version("v1", VersionStatus.DEPRECATED)
        manager.register_version("v2", VersionStatus.STABLE)

        assert manager.is_version_deprecated("v1") is True
        assert manager.is_version_deprecated("v2") is False

    def test_get_version_info(self):
        """Test getting version info."""
        manager = APIVersionManager()

        manager.register_version("v1", VersionStatus.STABLE, description="Version 1")

        info = manager.get_version_info("v1")

        assert info is not None
        assert info.version == "v1"
        assert info.description == "Version 1"

    def test_get_all_versions(self):
        """Test getting all versions."""
        manager = APIVersionManager()

        manager.register_version("v1", VersionStatus.STABLE)
        manager.register_version("v2", VersionStatus.BETA)
        manager.register_version("v3", VersionStatus.DEVELOPMENT)

        versions = manager.get_all_versions()

        assert len(versions) == 3
        assert all(isinstance(v, VersionInfo) for v in versions)

    def test_get_supported_versions(self):
        """Test getting supported versions."""
        manager = APIVersionManager()

        manager.register_version("v1", VersionStatus.STABLE)
        manager.register_version("v2", VersionStatus.DEPRECATED)
        manager.register_version("v3", VersionStatus.SUNSET)

        supported = manager.get_supported_versions()

        assert "v1" in supported
        assert "v2" in supported
        assert "v3" not in supported

    def test_deprecate_version(self):
        """Test deprecating a version."""
        manager = APIVersionManager()

        manager.register_version("v1", VersionStatus.STABLE)

        sunset_date = date.today() + timedelta(days=180)
        manager.deprecate_version("v1", sunset_date=sunset_date)

        info = manager.get_version_info("v1")
        assert info.status == VersionStatus.DEPRECATED
        assert info.deprecation_date == date.today()
        assert info.sunset_date == sunset_date

    def test_deprecate_unregistered_version_raises_error(self):
        """Test deprecating unregistered version raises error."""
        manager = APIVersionManager()

        with pytest.raises(ValueError, match="not registered"):
            manager.deprecate_version("v999")


class TestAPIVersionMiddleware:
    """Test API version middleware."""

    def create_test_app(self, version_manager=None):
        """Create test FastAPI app with version middleware."""
        app = FastAPI()

        if version_manager is None:
            version_manager = APIVersionManager()
            version_manager.register_version("v1", VersionStatus.STABLE)
            version_manager.register_version("v2", VersionStatus.STABLE)

        app.add_middleware(
            APIVersionMiddleware,
            version_manager=version_manager
        )

        @app.get("/v1/test")
        async def test_v1(request: Request):
            return {
                "version": request.state.api_version,
                "message": "v1 endpoint"
            }

        @app.get("/v2/test")
        async def test_v2(request: Request):
            return {
                "version": request.state.api_version,
                "message": "v2 endpoint"
            }

        return app, version_manager

    def test_extract_version_from_url(self):
        """Test extracting version from URL."""
        app, manager = self.create_test_app()
        client = TestClient(app)

        response = client.get("/v1/test")

        assert response.status_code == 200
        assert response.json()["version"] == "v1"

    def test_version_header_added_to_response(self):
        """Test version header is added to response."""
        app, manager = self.create_test_app()
        client = TestClient(app)

        response = client.get("/v1/test")

        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v1"

    def test_deprecated_version_headers(self):
        """Test deprecated version adds deprecation headers."""
        manager = APIVersionManager()
        manager.register_version("v1", VersionStatus.STABLE)

        # Deprecate v1
        sunset_date = date.today() + timedelta(days=180)
        manager.deprecate_version("v1", sunset_date=sunset_date)

        app, _ = self.create_test_app(version_manager=manager)
        client = TestClient(app)

        response = client.get("/v1/test")

        assert response.headers["X-API-Deprecated"] == "true"
        assert "X-API-Deprecation-Date" in response.headers
        assert "X-API-Sunset-Date" in response.headers

    def test_stable_version_not_deprecated_header(self):
        """Test stable version has deprecated=false header."""
        app, manager = self.create_test_app()
        client = TestClient(app)

        response = client.get("/v1/test")

        assert response.headers["X-API-Deprecated"] == "false"

    def test_unsupported_version_returns_400(self):
        """Test requesting unsupported version returns 400."""
        app, manager = self.create_test_app()
        client = TestClient(app)

        response = client.get("/v999/test")

        assert response.status_code == 400
        assert "Unsupported API version" in response.json()["detail"]

    def test_sunset_version_not_supported(self):
        """Test sunset version returns 400."""
        manager = APIVersionManager()
        manager.register_version("v1", VersionStatus.SUNSET)

        app, _ = self.create_test_app(version_manager=manager)
        client = TestClient(app)

        response = client.get("/v1/test")

        assert response.status_code == 400

    def test_version_status_header(self):
        """Test X-API-Status header is added."""
        manager = APIVersionManager()
        manager.register_version("v1", VersionStatus.BETA)

        app, _ = self.create_test_app(version_manager=manager)
        client = TestClient(app)

        response = client.get("/v1/test")

        assert "X-API-Status" in response.headers
        assert response.headers["X-API-Status"] == "beta"


class TestSetupAPIVersioning:
    """Test setup_api_versioning helper function."""

    def test_setup_basic_versioning(self):
        """Test basic versioning setup."""
        app = FastAPI()

        setup_api_versioning(
            app,
            supported_versions=["v1", "v2"],
            default_version="v1"
        )

        # Check version manager is configured
        manager = get_version_manager()

        assert manager.get_default_version() == "v1"
        assert "v1" in manager.get_supported_versions()
        assert "v2" in manager.get_supported_versions()

    def test_setup_with_deprecated_versions(self):
        """Test setup with deprecated versions."""
        app = FastAPI()

        setup_api_versioning(
            app,
            supported_versions=["v1", "v2"],
            default_version="v2",
            deprecated_versions={
                "v1": {
                    "deprecation_date": date(2026, 1, 1),
                    "sunset_date": date(2026, 7, 1)
                }
            }
        )

        manager = get_version_manager()

        assert manager.is_version_deprecated("v1") is True
        assert manager.is_version_deprecated("v2") is False

    def test_version_endpoint_created(self):
        """Test /version endpoint is created."""
        app = FastAPI()

        setup_api_versioning(
            app,
            supported_versions=["v1", "v2"],
            default_version="v2"
        )

        client = TestClient(app)
        response = client.get("/version")

        assert response.status_code == 200
        data = response.json()

        assert data["default"] == "v2"
        assert "v1" in data["supported"]
        assert "v2" in data["supported"]
        assert "versions" in data


class TestVersionLifecycle:
    """Test version lifecycle scenarios."""

    def test_development_to_stable_lifecycle(self):
        """Test transitioning version from development to stable."""
        manager = APIVersionManager()

        # Register as development
        manager.register_version("v2", VersionStatus.DEVELOPMENT)

        assert manager.get_version_info("v2").status == VersionStatus.DEVELOPMENT

        # Update to beta
        manager.versions["v2"].status = VersionStatus.BETA

        assert manager.get_version_info("v2").status == VersionStatus.BETA

        # Update to stable
        manager.versions["v2"].status = VersionStatus.STABLE

        assert manager.get_version_info("v2").status == VersionStatus.STABLE

    def test_stable_to_deprecated_to_sunset(self):
        """Test full lifecycle from stable to sunset."""
        manager = APIVersionManager()

        # Start as stable
        manager.register_version("v1", VersionStatus.STABLE)

        # Deprecate
        manager.deprecate_version("v1", sunset_date=date.today() + timedelta(days=180))

        assert manager.is_version_deprecated("v1") is True
        assert manager.is_version_supported("v1") is True

        # Sunset
        manager.versions["v1"].status = VersionStatus.SUNSET

        assert manager.is_version_supported("v1") is False


class TestVersionComparison:
    """Test version comparison logic."""

    def test_version_number_extraction(self):
        """Test extracting version number from version string."""
        import re

        def version_number(v: str) -> int:
            match = re.match(r"v(\d+)", v)
            return int(match.group(1)) if match else 0

        assert version_number("v1") == 1
        assert version_number("v2") == 2
        assert version_number("v10") == 10
        assert version_number("invalid") == 0


class TestGlobalVersionManager:
    """Test global version manager instance."""

    def test_get_version_manager_singleton(self):
        """Test get_version_manager returns singleton."""
        manager1 = get_version_manager()
        manager2 = get_version_manager()

        assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
