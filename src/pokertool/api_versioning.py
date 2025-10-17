#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Versioning Middleware and Utilities
========================================

Provides version management for PokerTool REST API with support for
URL-based and header-based versioning.

Features:
- URL path versioning (/v1/endpoint, /v2/endpoint)
- Header-based version negotiation (Accept-Version)
- Deprecation warnings
- Version lifecycle management
- Automatic version header injection

Module: pokertool.api_versioning
Version: 1.0.0
"""

from typing import Dict, List, Optional, Callable
from fastapi import Request, Response, HTTPException, Header
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class VersionStatus(str, Enum):
    """API version lifecycle status."""
    DEVELOPMENT = "development"
    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


@dataclass
class VersionInfo:
    """Information about an API version."""
    version: str
    status: VersionStatus
    release_date: Optional[date] = None
    deprecation_date: Optional[date] = None
    sunset_date: Optional[date] = None
    description: str = ""


class APIVersionManager:
    """
    Manages API version lifecycle and metadata.

    Features:
    - Version registration and tracking
    - Status management (development, stable, deprecated, etc.)
    - Deprecation and sunset date tracking
    - Version comparison and validation
    """

    def __init__(self):
        """Initialize version manager."""
        self.versions: Dict[str, VersionInfo] = {}
        self._default_version: Optional[str] = None

    def register_version(
        self,
        version: str,
        status: VersionStatus = VersionStatus.STABLE,
        release_date: Optional[date] = None,
        deprecation_date: Optional[date] = None,
        sunset_date: Optional[date] = None,
        description: str = ""
    ) -> None:
        """
        Register an API version.

        Args:
            version: Version identifier (e.g., "v1", "v2")
            status: Current lifecycle status
            release_date: When version was released
            deprecation_date: When version was deprecated
            sunset_date: When version will be removed
            description: Version description
        """
        self.versions[version] = VersionInfo(
            version=version,
            status=status,
            release_date=release_date or date.today(),
            deprecation_date=deprecation_date,
            sunset_date=sunset_date,
            description=description
        )

        # Set first version as default
        if self._default_version is None:
            self._default_version = version

        logger.info(f"Registered API version: {version} (status: {status})")

    def set_default_version(self, version: str) -> None:
        """
        Set the default API version.

        Args:
            version: Version to set as default

        Raises:
            ValueError: If version not registered
        """
        if version not in self.versions:
            raise ValueError(f"Version {version} not registered")

        self._default_version = version
        logger.info(f"Set default API version: {version}")

    def get_default_version(self) -> str:
        """
        Get the default API version.

        Returns:
            Default version identifier
        """
        if not self._default_version:
            raise ValueError("No versions registered")

        return self._default_version

    def is_version_supported(self, version: str) -> bool:
        """
        Check if a version is supported.

        Args:
            version: Version to check

        Returns:
            True if version exists and is not sunset
        """
        if version not in self.versions:
            return False

        version_info = self.versions[version]
        return version_info.status != VersionStatus.SUNSET

    def is_version_deprecated(self, version: str) -> bool:
        """
        Check if a version is deprecated.

        Args:
            version: Version to check

        Returns:
            True if version is deprecated
        """
        if version not in self.versions:
            return False

        return self.versions[version].status == VersionStatus.DEPRECATED

    def get_version_info(self, version: str) -> Optional[VersionInfo]:
        """
        Get information about a version.

        Args:
            version: Version identifier

        Returns:
            VersionInfo object or None if not found
        """
        return self.versions.get(version)

    def get_all_versions(self) -> List[VersionInfo]:
        """
        Get all registered versions.

        Returns:
            List of VersionInfo objects
        """
        return list(self.versions.values())

    def get_supported_versions(self) -> List[str]:
        """
        Get list of supported version identifiers.

        Returns:
            List of version strings (excluding sunset versions)
        """
        return [
            v.version for v in self.versions.values()
            if v.status != VersionStatus.SUNSET
        ]

    def deprecate_version(
        self,
        version: str,
        deprecation_date: Optional[date] = None,
        sunset_date: Optional[date] = None
    ) -> None:
        """
        Mark a version as deprecated.

        Args:
            version: Version to deprecate
            deprecation_date: Date of deprecation (default: today)
            sunset_date: Date when version will be sunset

        Raises:
            ValueError: If version not registered
        """
        if version not in self.versions:
            raise ValueError(f"Version {version} not registered")

        version_info = self.versions[version]
        version_info.status = VersionStatus.DEPRECATED
        version_info.deprecation_date = deprecation_date or date.today()

        if sunset_date:
            version_info.sunset_date = sunset_date

        logger.warning(f"Version {version} deprecated (sunset: {sunset_date})")


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API version management.

    Features:
    - Extracts version from URL path or headers
    - Validates version support
    - Adds version headers to responses
    - Handles deprecation warnings
    """

    def __init__(
        self,
        app: ASGIApp,
        version_manager: APIVersionManager,
        version_header_name: str = "Accept-Version",
        url_version_pattern: str = r"/v(\d+)/",
        enable_header_versioning: bool = False
    ):
        """
        Initialize version middleware.

        Args:
            app: ASGI application
            version_manager: Version manager instance
            version_header_name: Header name for version negotiation
            url_version_pattern: Regex pattern to extract version from URL
            enable_header_versioning: Enable header-based versioning
        """
        super().__init__(app)
        self.version_manager = version_manager
        self.version_header_name = version_header_name
        self.url_version_pattern = re.compile(url_version_pattern)
        self.enable_header_versioning = enable_header_versioning

    def extract_version_from_url(self, path: str) -> Optional[str]:
        """
        Extract version from URL path.

        Args:
            path: Request URL path

        Returns:
            Version string (e.g., "v1") or None
        """
        match = self.url_version_pattern.search(path)
        if match:
            return f"v{match.group(1)}"
        return None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with version management.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response with version headers
        """
        # Extract version from URL
        url_version = self.extract_version_from_url(request.url.path)

        # Extract version from header (if enabled)
        header_version = None
        if self.enable_header_versioning:
            header_version = request.headers.get(self.version_header_name)

        # Determine version to use
        version = url_version or header_version or self.version_manager.get_default_version()

        # Validate version is supported
        if not self.version_manager.is_version_supported(version):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported API version: {version}. Supported versions: {self.version_manager.get_supported_versions()}"
            )

        # Store version in request state
        request.state.api_version = version

        # Process request
        response = await call_next(request)

        # Add version headers to response
        version_info = self.version_manager.get_version_info(version)

        if version_info:
            response.headers["X-API-Version"] = version

            # Add deprecation headers if version is deprecated
            if version_info.status == VersionStatus.DEPRECATED:
                response.headers["X-API-Deprecated"] = "true"

                if version_info.deprecation_date:
                    response.headers["X-API-Deprecation-Date"] = version_info.deprecation_date.isoformat()

                if version_info.sunset_date:
                    response.headers["X-API-Sunset-Date"] = version_info.sunset_date.isoformat()

                    # Add Link header to successor version
                    successor_version = self._get_successor_version(version)
                    if successor_version:
                        response.headers["Link"] = f"</{successor_version}/docs>; rel=\"successor-version\""

            else:
                response.headers["X-API-Deprecated"] = "false"

            # Add status header
            response.headers["X-API-Status"] = version_info.status.value

        return response

    def _get_successor_version(self, version: str) -> Optional[str]:
        """
        Get the successor version for a deprecated version.

        Args:
            version: Current version

        Returns:
            Successor version identifier or None
        """
        # Simple logic: increment version number
        # e.g., v1 → v2, v2 → v3
        match = re.match(r"v(\d+)", version)
        if match:
            version_num = int(match.group(1))
            successor = f"v{version_num + 1}"

            if self.version_manager.is_version_supported(successor):
                return successor

        return None


# Global version manager instance
_version_manager: Optional[APIVersionManager] = None


def get_version_manager() -> APIVersionManager:
    """
    Get or create global version manager instance.

    Returns:
        Global APIVersionManager instance
    """
    global _version_manager
    if _version_manager is None:
        _version_manager = APIVersionManager()
    return _version_manager


# FastAPI dependency for version validation
async def require_version(
    request: Request,
    min_version: Optional[str] = None,
    max_version: Optional[str] = None
) -> str:
    """
    FastAPI dependency to require specific version range.

    Args:
        request: Current request
        min_version: Minimum required version
        max_version: Maximum allowed version

    Returns:
        Current API version

    Raises:
        HTTPException: If version requirements not met
    """
    current_version = getattr(request.state, 'api_version', None)

    if not current_version:
        raise HTTPException(
            status_code=400,
            detail="API version not specified"
        )

    # Simple version comparison (assumes v1, v2, v3, etc.)
    def version_number(v: str) -> int:
        match = re.match(r"v(\d+)", v)
        return int(match.group(1)) if match else 0

    current_num = version_number(current_version)

    if min_version:
        min_num = version_number(min_version)
        if current_num < min_num:
            raise HTTPException(
                status_code=400,
                detail=f"API version {current_version} is too old. Minimum: {min_version}"
            )

    if max_version:
        max_num = version_number(max_version)
        if current_num > max_num:
            raise HTTPException(
                status_code=400,
                detail=f"API version {current_version} is too new. Maximum: {max_version}"
            )

    return current_version


# Helper function to setup versioning for FastAPI app
def setup_api_versioning(
    app,
    supported_versions: List[str],
    default_version: str,
    deprecated_versions: Optional[Dict[str, dict]] = None
):
    """
    Setup API versioning for FastAPI application.

    Args:
        app: FastAPI application instance
        supported_versions: List of supported version identifiers
        default_version: Default version to use
        deprecated_versions: Dict of deprecated versions with deprecation info

    Example:
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
    """
    version_manager = get_version_manager()

    # Register supported versions
    for version in supported_versions:
        is_deprecated = deprecated_versions and version in deprecated_versions

        if is_deprecated:
            dep_info = deprecated_versions[version]
            version_manager.register_version(
                version=version,
                status=VersionStatus.DEPRECATED,
                deprecation_date=dep_info.get("deprecation_date"),
                sunset_date=dep_info.get("sunset_date")
            )
        else:
            version_manager.register_version(
                version=version,
                status=VersionStatus.STABLE
            )

    # Set default version
    version_manager.set_default_version(default_version)

    # Add middleware
    app.add_middleware(
        APIVersionMiddleware,
        version_manager=version_manager
    )

    # Add version info endpoint
    @app.get("/version")
    async def get_version_info():
        """Get API version information."""
        return {
            "default": version_manager.get_default_version(),
            "supported": version_manager.get_supported_versions(),
            "versions": [
                {
                    "version": v.version,
                    "status": v.status.value,
                    "release_date": v.release_date.isoformat() if v.release_date else None,
                    "deprecation_date": v.deprecation_date.isoformat() if v.deprecation_date else None,
                    "sunset_date": v.sunset_date.isoformat() if v.sunset_date else None,
                    "description": v.description
                }
                for v in version_manager.get_all_versions()
            ]
        }

    logger.info(f"API versioning configured: default={default_version}, supported={supported_versions}")
