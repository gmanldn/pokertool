#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Role-Based Access Control (RBAC) System
========================================

Provides comprehensive role-based access control for feature authorization.

RBAC allows flexible permission management through roles and permissions,
making it easy to control access to features, API endpoints, and resources.

Module: pokertool.rbac
Version: 1.0.0
"""

from typing import List, Set, Dict, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from fastapi import Request, HTTPException, status, Depends
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """
    System permissions for fine-grained access control.
    """
    # Hand analysis permissions
    ANALYZE_HAND = "analyze:hand"
    VIEW_ANALYSIS = "view:analysis"

    # Database permissions
    READ_DATABASE = "read:database"
    WRITE_DATABASE = "write:database"
    DELETE_DATABASE = "delete:database"

    # User management
    CREATE_USER = "create:user"
    READ_USER = "read:user"
    UPDATE_USER = "update:user"
    DELETE_USER = "delete:user"

    # Settings and configuration
    READ_SETTINGS = "read:settings"
    WRITE_SETTINGS = "write:settings"

    # GTO solver and training
    USE_GTO_SOLVER = "use:gto_solver"
    USE_TRAINER = "use:trainer"

    # Analytics and reports
    VIEW_ANALYTICS = "view:analytics"
    EXPORT_ANALYTICS = "export:analytics"

    # API access
    ACCESS_API = "access:api"
    ADMIN_API = "admin:api"

    # System administration
    MANAGE_SYSTEM = "manage:system"
    VIEW_LOGS = "view:logs"


class Role(str, Enum):
    """
    User roles with predefined permission sets.
    """
    # Basic user with limited access
    GUEST = "guest"

    # Standard user with full feature access
    USER = "user"

    # Power user with advanced features
    POWER_USER = "power_user"

    # Administrator with full system access
    ADMIN = "admin"

    # Read-only access for analysis
    ANALYST = "analyst"


@dataclass
class RoleDefinition:
    """Definition of a role with its permissions."""
    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)
    inherits_from: Optional[List[str]] = None


class RBACSystem:
    """
    Role-Based Access Control system implementation.

    Features:
    - Role hierarchy with permission inheritance
    - Fine-grained permission checking
    - Dynamic role assignment
    - Permission caching for performance
    """

    def __init__(self):
        """Initialize RBAC system with default roles."""
        self.roles: Dict[str, RoleDefinition] = {}
        self.user_roles: Dict[str, Set[str]] = {}  # user_id -> roles
        self._initialize_default_roles()

    def _initialize_default_roles(self) -> None:
        """Set up default role definitions."""
        # Guest role - minimal access
        self.define_role(
            Role.GUEST,
            "Guest user with read-only access",
            {
                Permission.VIEW_ANALYSIS,
                Permission.READ_SETTINGS,
            }
        )

        # User role - standard feature access
        self.define_role(
            Role.USER,
            "Standard user with full feature access",
            {
                Permission.ANALYZE_HAND,
                Permission.VIEW_ANALYSIS,
                Permission.READ_DATABASE,
                Permission.WRITE_DATABASE,
                Permission.READ_USER,
                Permission.UPDATE_USER,
                Permission.READ_SETTINGS,
                Permission.WRITE_SETTINGS,
                Permission.USE_GTO_SOLVER,
                Permission.USE_TRAINER,
                Permission.VIEW_ANALYTICS,
                Permission.ACCESS_API,
            },
            inherits_from=[Role.GUEST]
        )

        # Power user role - advanced features
        self.define_role(
            Role.POWER_USER,
            "Power user with advanced features",
            {
                Permission.DELETE_DATABASE,
                Permission.EXPORT_ANALYTICS,
            },
            inherits_from=[Role.USER]
        )

        # Analyst role - analytics focused
        self.define_role(
            Role.ANALYST,
            "Analyst with read and analytics access",
            {
                Permission.VIEW_ANALYSIS,
                Permission.READ_DATABASE,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_ANALYTICS,
                Permission.READ_SETTINGS,
            }
        )

        # Admin role - full system access
        self.define_role(
            Role.ADMIN,
            "Administrator with full system access",
            {
                Permission.CREATE_USER,
                Permission.DELETE_USER,
                Permission.MANAGE_SYSTEM,
                Permission.VIEW_LOGS,
                Permission.ADMIN_API,
            },
            inherits_from=[Role.POWER_USER]
        )

    def define_role(
        self,
        role: str,
        description: str,
        permissions: Set[Permission],
        inherits_from: Optional[List[str]] = None
    ) -> None:
        """
        Define a new role or update existing role.

        Args:
            role: Role identifier
            description: Human-readable description
            permissions: Set of permissions for this role
            inherits_from: List of roles to inherit permissions from
        """
        self.roles[role] = RoleDefinition(
            name=role,
            description=description,
            permissions=permissions,
            inherits_from=inherits_from
        )

    def get_role_permissions(self, role: str) -> Set[Permission]:
        """
        Get all permissions for a role including inherited permissions.

        Args:
            role: Role identifier

        Returns:
            Set of all permissions for the role
        """
        if role not in self.roles:
            logger.warning(f"Unknown role requested: {role}")
            return set()

        role_def = self.roles[role]
        permissions = role_def.permissions.copy()

        # Add inherited permissions
        if role_def.inherits_from:
            for parent_role in role_def.inherits_from:
                permissions.update(self.get_role_permissions(parent_role))

        return permissions

    def assign_role(self, user_id: str, role: str) -> None:
        """
        Assign a role to a user.

        Args:
            user_id: User identifier
            role: Role to assign
        """
        if role not in self.roles:
            raise ValueError(f"Unknown role: {role}")

        if user_id not in self.user_roles:
            self.user_roles[user_id] = set()

        self.user_roles[user_id].add(role)
        logger.info(f"Assigned role {role} to user {user_id}")

    def revoke_role(self, user_id: str, role: str) -> None:
        """
        Revoke a role from a user.

        Args:
            user_id: User identifier
            role: Role to revoke
        """
        if user_id in self.user_roles:
            self.user_roles[user_id].discard(role)
            logger.info(f"Revoked role {role} from user {user_id}")

    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """
        Get all permissions for a user based on their roles.

        Args:
            user_id: User identifier

        Returns:
            Set of all permissions user has
        """
        if user_id not in self.user_roles:
            # No roles assigned, return empty set
            return set()

        permissions = set()
        for role in self.user_roles[user_id]:
            permissions.update(self.get_role_permissions(role))

        return permissions

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user_id: User identifier
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        user_permissions = self.get_user_permissions(user_id)
        return permission in user_permissions

    def has_any_permission(self, user_id: str, permissions: List[Permission]) -> bool:
        """
        Check if user has any of the specified permissions.

        Args:
            user_id: User identifier
            permissions: List of permissions to check

        Returns:
            True if user has at least one permission
        """
        user_permissions = self.get_user_permissions(user_id)
        return any(perm in user_permissions for perm in permissions)

    def has_all_permissions(self, user_id: str, permissions: List[Permission]) -> bool:
        """
        Check if user has all of the specified permissions.

        Args:
            user_id: User identifier
            permissions: List of permissions to check

        Returns:
            True if user has all permissions
        """
        user_permissions = self.get_user_permissions(user_id)
        return all(perm in user_permissions for perm in permissions)

    def has_role(self, user_id: str, role: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            user_id: User identifier
            role: Role to check

        Returns:
            True if user has role
        """
        return user_id in self.user_roles and role in self.user_roles[user_id]


# Global RBAC instance
_rbac_system: Optional[RBACSystem] = None


def get_rbac_system() -> RBACSystem:
    """Get or create global RBAC system instance."""
    global _rbac_system
    if _rbac_system is None:
        _rbac_system = RBACSystem()
    return _rbac_system


# Dependency for FastAPI routes
def require_permission(permission: Permission):
    """
    FastAPI dependency to require specific permission.

    Usage:
        @app.get("/admin", dependencies=[Depends(require_permission(Permission.MANAGE_SYSTEM))])
        def admin_endpoint():
            return {"message": "Admin access granted"}

    Args:
        permission: Required permission

    Returns:
        Dependency function
    """
    def permission_checker(request: Request) -> None:
        # Get user ID from request (from JWT token, session, etc.)
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        rbac = get_rbac_system()
        if not rbac.has_permission(user_id, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission.value}"
            )

    return permission_checker


def require_role(role: str):
    """
    FastAPI dependency to require specific role.

    Usage:
        @app.get("/admin", dependencies=[Depends(require_role(Role.ADMIN))])
        def admin_endpoint():
            return {"message": "Admin access granted"}

    Args:
        role: Required role

    Returns:
        Dependency function
    """
    def role_checker(request: Request) -> None:
        user_id = getattr(request.state, 'user_id', None)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        rbac = get_rbac_system()
        if not rbac.has_role(user_id, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required role: {role}"
            )

    return role_checker


# Decorator for permission checking
def requires_permission(permission: Permission):
    """
    Decorator to check permission for a function.

    Usage:
        @requires_permission(Permission.ANALYZE_HAND)
        def analyze_hand(user_id: str, hand_data: dict):
            # Function implementation
            pass

    Args:
        permission: Required permission

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract user_id from args or kwargs
            user_id = kwargs.get('user_id') or (args[0] if args else None)

            if not user_id:
                raise ValueError("user_id required for permission check")

            rbac = get_rbac_system()
            if not rbac.has_permission(user_id, permission):
                raise PermissionError(f"Missing required permission: {permission.value}")

            return func(*args, **kwargs)

        return wrapper
    return decorator
