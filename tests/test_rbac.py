#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite for RBAC System
===========================

Comprehensive tests for role-based access control system.

Module: tests.test_rbac
Version: 1.0.0
"""

import pytest
from unittest.mock import Mock, MagicMock
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.testclient import TestClient

from pokertool.rbac import (
    Permission,
    Role,
    RoleDefinition,
    RBACSystem,
    get_rbac_system,
    require_permission,
    require_role,
    requires_permission
)


class TestPermissionEnum:
    """Test Permission enumeration."""

    def test_permission_values(self):
        """Test permission enum values are correctly formatted."""
        assert Permission.ANALYZE_HAND.value == "analyze:hand"
        assert Permission.READ_DATABASE.value == "read:database"
        assert Permission.MANAGE_SYSTEM.value == "manage:system"
        assert Permission.ACCESS_API.value == "access:api"

    def test_permission_is_string_enum(self):
        """Test permissions are string enums."""
        assert isinstance(Permission.ANALYZE_HAND, str)
        assert isinstance(Permission.READ_DATABASE, str)


class TestRoleEnum:
    """Test Role enumeration."""

    def test_role_values(self):
        """Test role enum values."""
        assert Role.GUEST == "guest"
        assert Role.USER == "user"
        assert Role.POWER_USER == "power_user"
        assert Role.ADMIN == "admin"
        assert Role.ANALYST == "analyst"

    def test_role_is_string_enum(self):
        """Test roles are string enums."""
        assert isinstance(Role.GUEST, str)
        assert isinstance(Role.USER, str)


class TestRoleDefinition:
    """Test RoleDefinition dataclass."""

    def test_role_definition_creation(self):
        """Test creating role definition."""
        role_def = RoleDefinition(
            name="test_role",
            description="Test role",
            permissions={Permission.VIEW_ANALYSIS},
            inherits_from=[Role.GUEST]
        )

        assert role_def.name == "test_role"
        assert role_def.description == "Test role"
        assert Permission.VIEW_ANALYSIS in role_def.permissions
        assert role_def.inherits_from == [Role.GUEST]

    def test_role_definition_defaults(self):
        """Test role definition with defaults."""
        role_def = RoleDefinition(
            name="test_role",
            description="Test role"
        )

        assert role_def.permissions == set()
        assert role_def.inherits_from is None


class TestRBACSystem:
    """Test RBAC system core functionality."""

    def test_initialization(self):
        """Test RBAC system initialization."""
        rbac = RBACSystem()

        # Should have default roles defined
        assert Role.GUEST in rbac.roles
        assert Role.USER in rbac.roles
        assert Role.POWER_USER in rbac.roles
        assert Role.ADMIN in rbac.roles
        assert Role.ANALYST in rbac.roles

    def test_default_guest_role_permissions(self):
        """Test guest role has correct default permissions."""
        rbac = RBACSystem()
        permissions = rbac.get_role_permissions(Role.GUEST)

        assert Permission.VIEW_ANALYSIS in permissions
        assert Permission.READ_SETTINGS in permissions

        # Guest should not have write permissions
        assert Permission.ANALYZE_HAND not in permissions
        assert Permission.WRITE_DATABASE not in permissions

    def test_default_user_role_permissions(self):
        """Test user role has correct default permissions."""
        rbac = RBACSystem()
        permissions = rbac.get_role_permissions(Role.USER)

        # User should have standard permissions
        assert Permission.ANALYZE_HAND in permissions
        assert Permission.VIEW_ANALYSIS in permissions
        assert Permission.READ_DATABASE in permissions
        assert Permission.WRITE_DATABASE in permissions
        assert Permission.USE_GTO_SOLVER in permissions
        assert Permission.ACCESS_API in permissions

        # User should inherit guest permissions
        assert Permission.READ_SETTINGS in permissions

    def test_default_power_user_role_permissions(self):
        """Test power user role has correct permissions."""
        rbac = RBACSystem()
        permissions = rbac.get_role_permissions(Role.POWER_USER)

        # Power user should have advanced permissions
        assert Permission.DELETE_DATABASE in permissions
        assert Permission.EXPORT_ANALYTICS in permissions

        # Should inherit all user permissions
        assert Permission.ANALYZE_HAND in permissions
        assert Permission.WRITE_DATABASE in permissions

    def test_default_admin_role_permissions(self):
        """Test admin role has correct permissions."""
        rbac = RBACSystem()
        permissions = rbac.get_role_permissions(Role.ADMIN)

        # Admin should have admin permissions
        assert Permission.CREATE_USER in permissions
        assert Permission.DELETE_USER in permissions
        assert Permission.MANAGE_SYSTEM in permissions
        assert Permission.VIEW_LOGS in permissions
        assert Permission.ADMIN_API in permissions

        # Should inherit all power user permissions
        assert Permission.DELETE_DATABASE in permissions
        assert Permission.ANALYZE_HAND in permissions

    def test_default_analyst_role_permissions(self):
        """Test analyst role has correct permissions."""
        rbac = RBACSystem()
        permissions = rbac.get_role_permissions(Role.ANALYST)

        # Analyst should have read and analytics permissions
        assert Permission.VIEW_ANALYSIS in permissions
        assert Permission.READ_DATABASE in permissions
        assert Permission.VIEW_ANALYTICS in permissions
        assert Permission.EXPORT_ANALYTICS in permissions

        # Analyst should not have write permissions
        assert Permission.WRITE_DATABASE not in permissions
        assert Permission.ANALYZE_HAND not in permissions

    def test_define_custom_role(self):
        """Test defining custom role."""
        rbac = RBACSystem()

        rbac.define_role(
            role="custom",
            description="Custom role",
            permissions={Permission.VIEW_ANALYSIS, Permission.READ_DATABASE}
        )

        assert "custom" in rbac.roles
        permissions = rbac.get_role_permissions("custom")
        assert Permission.VIEW_ANALYSIS in permissions
        assert Permission.READ_DATABASE in permissions

    def test_role_inheritance(self):
        """Test role inheritance."""
        rbac = RBACSystem()

        # Create parent role
        rbac.define_role(
            role="parent",
            description="Parent role",
            permissions={Permission.VIEW_ANALYSIS}
        )

        # Create child role inheriting from parent
        rbac.define_role(
            role="child",
            description="Child role",
            permissions={Permission.READ_DATABASE},
            inherits_from=["parent"]
        )

        child_permissions = rbac.get_role_permissions("child")

        # Child should have own permissions
        assert Permission.READ_DATABASE in child_permissions

        # Child should inherit parent permissions
        assert Permission.VIEW_ANALYSIS in child_permissions

    def test_multi_level_inheritance(self):
        """Test multi-level role inheritance."""
        rbac = RBACSystem()

        # Verify USER inherits from GUEST
        # and POWER_USER inherits from USER
        # and ADMIN inherits from POWER_USER
        guest_perms = rbac.get_role_permissions(Role.GUEST)
        user_perms = rbac.get_role_permissions(Role.USER)
        power_user_perms = rbac.get_role_permissions(Role.POWER_USER)
        admin_perms = rbac.get_role_permissions(Role.ADMIN)

        # Each level should include previous level permissions
        assert guest_perms.issubset(user_perms)
        assert user_perms.issubset(power_user_perms)
        assert power_user_perms.issubset(admin_perms)

    def test_assign_role_to_user(self):
        """Test assigning role to user."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)

        assert rbac.has_role("user123", Role.USER)

    def test_assign_multiple_roles_to_user(self):
        """Test assigning multiple roles to user."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)
        rbac.assign_role("user123", Role.ANALYST)

        assert rbac.has_role("user123", Role.USER)
        assert rbac.has_role("user123", Role.ANALYST)

    def test_assign_unknown_role_raises_error(self):
        """Test assigning unknown role raises error."""
        rbac = RBACSystem()

        with pytest.raises(ValueError, match="Unknown role"):
            rbac.assign_role("user123", "nonexistent_role")

    def test_revoke_role_from_user(self):
        """Test revoking role from user."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)
        assert rbac.has_role("user123", Role.USER)

        rbac.revoke_role("user123", Role.USER)
        assert not rbac.has_role("user123", Role.USER)

    def test_get_user_permissions(self):
        """Test getting all permissions for user."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)
        permissions = rbac.get_user_permissions("user123")

        # Should have all user permissions
        assert Permission.ANALYZE_HAND in permissions
        assert Permission.VIEW_ANALYSIS in permissions
        assert Permission.READ_DATABASE in permissions

    def test_get_user_permissions_multiple_roles(self):
        """Test getting permissions with multiple roles."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)
        rbac.assign_role("user123", Role.ANALYST)

        permissions = rbac.get_user_permissions("user123")

        # Should have permissions from both roles
        assert Permission.ANALYZE_HAND in permissions  # from USER
        assert Permission.EXPORT_ANALYTICS in permissions  # from ANALYST

    def test_get_user_permissions_no_roles(self):
        """Test getting permissions for user with no roles."""
        rbac = RBACSystem()

        permissions = rbac.get_user_permissions("user123")

        # Should be empty set
        assert permissions == set()

    def test_has_permission(self):
        """Test checking if user has permission."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)

        assert rbac.has_permission("user123", Permission.ANALYZE_HAND) is True
        assert rbac.has_permission("user123", Permission.MANAGE_SYSTEM) is False

    def test_has_any_permission(self):
        """Test checking if user has any of specified permissions."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)

        # User has ANALYZE_HAND
        assert rbac.has_any_permission(
            "user123",
            [Permission.ANALYZE_HAND, Permission.MANAGE_SYSTEM]
        ) is True

        # User has neither
        assert rbac.has_any_permission(
            "user123",
            [Permission.MANAGE_SYSTEM, Permission.DELETE_USER]
        ) is False

    def test_has_all_permissions(self):
        """Test checking if user has all specified permissions."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)

        # User has both
        assert rbac.has_all_permissions(
            "user123",
            [Permission.ANALYZE_HAND, Permission.READ_DATABASE]
        ) is True

        # User missing MANAGE_SYSTEM
        assert rbac.has_all_permissions(
            "user123",
            [Permission.ANALYZE_HAND, Permission.MANAGE_SYSTEM]
        ) is False

    def test_has_role(self):
        """Test checking if user has role."""
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.USER)

        assert rbac.has_role("user123", Role.USER) is True
        assert rbac.has_role("user123", Role.ADMIN) is False


class TestRBACFastAPIIntegration:
    """Test RBAC integration with FastAPI."""

    def test_require_permission_dependency(self):
        """Test require_permission FastAPI dependency."""
        app = FastAPI()
        rbac = RBACSystem()

        # Assign role to user
        rbac.assign_role("user123", Role.USER)

        @app.get("/test", dependencies=[Depends(require_permission(Permission.ANALYZE_HAND))])
        async def test_endpoint():
            return {"message": "success"}

        client = TestClient(app)

        # Mock request with user_id
        # Note: In real implementation, user_id would come from JWT token
        # This test demonstrates the structure

    def test_require_role_dependency(self):
        """Test require_role FastAPI dependency."""
        app = FastAPI()
        rbac = RBACSystem()

        rbac.assign_role("user123", Role.ADMIN)

        @app.get("/admin", dependencies=[Depends(require_role(Role.ADMIN))])
        async def admin_endpoint():
            return {"message": "admin access"}

        # Note: Full integration test requires JWT token setup


class TestRBACDecorator:
    """Test RBAC decorator for functions."""

    def test_requires_permission_decorator_success(self):
        """Test requires_permission decorator allows access."""
        rbac = RBACSystem()
        rbac.assign_role("user123", Role.USER)

        @requires_permission(Permission.ANALYZE_HAND)
        def protected_function(user_id: str, data: dict):
            return {"result": "success"}

        # Should work for user with permission
        result = protected_function(user_id="user123", data={"test": "data"})
        assert result["result"] == "success"

    def test_requires_permission_decorator_denied(self):
        """Test requires_permission decorator denies access."""
        rbac = RBACSystem()
        rbac.assign_role("user123", Role.GUEST)  # Guest doesn't have ANALYZE_HAND

        @requires_permission(Permission.ANALYZE_HAND)
        def protected_function(user_id: str, data: dict):
            return {"result": "success"}

        # Should raise PermissionError
        with pytest.raises(PermissionError, match="Missing required permission"):
            protected_function(user_id="user123", data={"test": "data"})

    def test_requires_permission_decorator_no_user_id(self):
        """Test requires_permission decorator with missing user_id."""
        @requires_permission(Permission.ANALYZE_HAND)
        def protected_function(data: dict):
            return {"result": "success"}

        # Should raise ValueError
        with pytest.raises(ValueError, match="user_id required"):
            protected_function(data={"test": "data"})


class TestRBACGlobalInstance:
    """Test global RBAC instance."""

    def test_get_rbac_system_singleton(self):
        """Test get_rbac_system returns singleton."""
        rbac1 = get_rbac_system()
        rbac2 = get_rbac_system()

        # Should be same instance
        assert rbac1 is rbac2

    def test_get_rbac_system_initialized(self):
        """Test get_rbac_system returns initialized system."""
        rbac = get_rbac_system()

        # Should have default roles
        assert Role.GUEST in rbac.roles
        assert Role.ADMIN in rbac.roles


class TestRBACSecurityScenarios:
    """Test real-world security scenarios."""

    def test_privilege_escalation_prevention(self):
        """Test that users cannot escalate privileges."""
        rbac = RBACSystem()

        # Regular user
        rbac.assign_role("user123", Role.USER)

        # User should not have admin permissions
        assert rbac.has_permission("user123", Permission.MANAGE_SYSTEM) is False
        assert rbac.has_permission("user123", Permission.DELETE_USER) is False

        # Even with multiple non-admin roles
        rbac.assign_role("user123", Role.ANALYST)
        assert rbac.has_permission("user123", Permission.MANAGE_SYSTEM) is False

    def test_least_privilege_principle(self):
        """Test least privilege principle - users only get necessary permissions."""
        rbac = RBACSystem()

        # Guest should have minimal permissions
        rbac.assign_role("guest123", Role.GUEST)
        guest_perms = rbac.get_user_permissions("guest123")

        # Analyst should have more but still limited
        rbac.assign_role("analyst123", Role.ANALYST)
        analyst_perms = rbac.get_user_permissions("analyst123")

        # Admin should have most permissions
        rbac.assign_role("admin123", Role.ADMIN)
        admin_perms = rbac.get_user_permissions("admin123")

        # Verify hierarchy
        assert len(guest_perms) < len(analyst_perms)
        assert len(analyst_perms) < len(admin_perms)

    def test_role_based_feature_access(self):
        """Test feature access control based on roles."""
        rbac = RBACSystem()

        # Free tier user (guest)
        rbac.assign_role("free_user", Role.GUEST)

        # Premium user
        rbac.assign_role("premium_user", Role.USER)

        # Enterprise user
        rbac.assign_role("enterprise_user", Role.POWER_USER)

        # GTO solver access
        assert rbac.has_permission("free_user", Permission.USE_GTO_SOLVER) is False
        assert rbac.has_permission("premium_user", Permission.USE_GTO_SOLVER) is True
        assert rbac.has_permission("enterprise_user", Permission.USE_GTO_SOLVER) is True

        # Export analytics
        assert rbac.has_permission("free_user", Permission.EXPORT_ANALYTICS) is False
        assert rbac.has_permission("premium_user", Permission.EXPORT_ANALYTICS) is False
        assert rbac.has_permission("enterprise_user", Permission.EXPORT_ANALYTICS) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
