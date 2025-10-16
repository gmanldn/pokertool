#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PokerTool RBAC System Usage Examples
=====================================

This script demonstrates role-based access control patterns for the PokerTool application.

Run this script:
    python examples/rbac_example.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pokertool.rbac import (
    Permission,
    Role,
    RBACSystem,
    get_rbac_system,
    requires_permission
)


def example_basic_setup():
    """Example 1: Basic RBAC setup and user role assignment."""
    print("\n=== Example 1: Basic RBAC Setup ===\n")

    # Get the global RBAC system instance
    rbac = get_rbac_system()

    # Assign roles to users
    rbac.assign_role("user_001", Role.GUEST)
    rbac.assign_role("user_002", Role.USER)
    rbac.assign_role("user_003", Role.ADMIN)

    print("✓ Roles assigned:")
    print(f"  user_001: {Role.GUEST}")
    print(f"  user_002: {Role.USER}")
    print(f"  user_003: {Role.ADMIN}")

    # Check user roles
    for user_id in ["user_001", "user_002", "user_003"]:
        has_admin = rbac.has_role(user_id, Role.ADMIN)
        print(f"\n  {user_id} is admin: {has_admin}")


def example_permission_checking():
    """Example 2: Checking user permissions."""
    print("\n=== Example 2: Permission Checking ===\n")

    rbac = get_rbac_system()

    # Assign roles
    rbac.assign_role("free_user", Role.GUEST)
    rbac.assign_role("premium_user", Role.USER)
    rbac.assign_role("power_user", Role.POWER_USER)

    # Check various permissions
    users = ["free_user", "premium_user", "power_user"]
    permissions_to_check = [
        Permission.VIEW_ANALYSIS,
        Permission.ANALYZE_HAND,
        Permission.USE_GTO_SOLVER,
        Permission.DELETE_DATABASE,
        Permission.MANAGE_SYSTEM
    ]

    print("Permission Matrix:")
    print(f"{'User':<15} {'Permission':<25} {'Granted'}")
    print("-" * 50)

    for user in users:
        for perm in permissions_to_check:
            has_perm = rbac.has_permission(user, perm)
            status = "✓" if has_perm else "✗"
            print(f"{user:<15} {perm.value:<25} {status}")


def example_role_hierarchy():
    """Example 3: Demonstrating role hierarchy and inheritance."""
    print("\n=== Example 3: Role Hierarchy ===\n")

    rbac = get_rbac_system()

    # Assign different role levels
    rbac.assign_role("user_guest", Role.GUEST)
    rbac.assign_role("user_standard", Role.USER)
    rbac.assign_role("user_power", Role.POWER_USER)
    rbac.assign_role("user_admin", Role.ADMIN)

    # Get permissions for each role
    roles = [Role.GUEST, Role.USER, Role.POWER_USER, Role.ADMIN]

    print("Role Hierarchy (permissions increase with each level):\n")

    for role in roles:
        perms = rbac.get_role_permissions(role)
        print(f"{role:<15} - {len(perms)} permissions")

        # Show sample permissions
        sample_perms = list(perms)[:3]
        for perm in sample_perms:
            print(f"  - {perm.value}")

        print()

    # Demonstrate inheritance
    print("Inheritance Example:")
    admin_perms = rbac.get_role_permissions(Role.ADMIN)
    user_perms = rbac.get_role_permissions(Role.USER)

    print(f"  ADMIN has {len(admin_perms)} permissions")
    print(f"  USER has {len(user_perms)} permissions")
    print(f"  ADMIN inherits all USER permissions: {user_perms.issubset(admin_perms)}")


def example_custom_roles():
    """Example 4: Creating custom roles."""
    print("\n=== Example 4: Custom Roles ===\n")

    rbac = get_rbac_system()

    # Define custom role for premium subscription
    rbac.define_role(
        role="premium_subscriber",
        description="Premium tier with advanced features",
        permissions={
            Permission.ANALYZE_HAND,
            Permission.VIEW_ANALYSIS,
            Permission.USE_GTO_SOLVER,
            Permission.USE_TRAINER,
            Permission.VIEW_ANALYTICS,
            Permission.EXPORT_ANALYTICS,
        },
        inherits_from=[Role.USER]
    )

    print("✓ Created custom role: premium_subscriber")

    # Assign custom role
    rbac.assign_role("subscriber_001", "premium_subscriber")

    # Check permissions
    perms = rbac.get_user_permissions("subscriber_001")
    print(f"\nPremium subscriber has {len(perms)} total permissions:")

    for perm in sorted(perms, key=lambda p: p.value)[:5]:
        print(f"  - {perm.value}")


def example_multiple_roles():
    """Example 5: Users with multiple roles."""
    print("\n=== Example 5: Multiple Roles per User ===\n")

    rbac = get_rbac_system()

    # Assign multiple roles to one user
    user_id = "analyst_dev"

    rbac.assign_role(user_id, Role.ANALYST)
    rbac.assign_role(user_id, Role.USER)

    print(f"User '{user_id}' has multiple roles:")
    print(f"  - {Role.ANALYST}")
    print(f"  - {Role.USER}")

    # Get combined permissions
    perms = rbac.get_user_permissions(user_id)
    print(f"\nTotal unique permissions: {len(perms)}")

    # Demonstrate permission union
    analyst_perms = rbac.get_role_permissions(Role.ANALYST)
    user_perms = rbac.get_role_permissions(Role.USER)

    print(f"\nPermission breakdown:")
    print(f"  ANALYST role: {len(analyst_perms)} permissions")
    print(f"  USER role: {len(user_perms)} permissions")
    print(f"  Combined (union): {len(perms)} permissions")


def example_permission_groups():
    """Example 6: Checking groups of permissions."""
    print("\n=== Example 6: Permission Groups ===\n")

    rbac = get_rbac_system()

    rbac.assign_role("user_test", Role.USER)

    # Check if user has ANY of these permissions
    analytics_perms = [
        Permission.VIEW_ANALYTICS,
        Permission.EXPORT_ANALYTICS
    ]

    has_any_analytics = rbac.has_any_permission("user_test", analytics_perms)
    print(f"User has any analytics permission: {has_any_analytics}")

    # Check if user has ALL of these permissions
    basic_perms = [
        Permission.ANALYZE_HAND,
        Permission.VIEW_ANALYSIS,
        Permission.READ_DATABASE
    ]

    has_all_basic = rbac.has_all_permissions("user_test", basic_perms)
    print(f"User has all basic permissions: {has_all_basic}")

    # Admin permissions check
    admin_perms = [
        Permission.MANAGE_SYSTEM,
        Permission.DELETE_USER,
        Permission.VIEW_LOGS
    ]

    has_all_admin = rbac.has_all_permissions("user_test", admin_perms)
    print(f"User has all admin permissions: {has_all_admin}")


@requires_permission(Permission.ANALYZE_HAND)
def protected_function(user_id: str, hand_data: dict):
    """Example protected function using decorator."""
    return {
        "user_id": user_id,
        "result": f"Analyzed hand: {hand_data.get('cards')}",
        "recommendation": "raise"
    }


def example_function_decorators():
    """Example 7: Using permission decorators."""
    print("\n=== Example 7: Function Decorators ===\n")

    rbac = get_rbac_system()

    # User with permission
    rbac.assign_role("allowed_user", Role.USER)

    # User without permission
    rbac.assign_role("denied_user", Role.GUEST)

    # Try calling protected function with different users
    print("Calling protected function:")

    # This should succeed
    try:
        result = protected_function(
            user_id="allowed_user",
            hand_data={"cards": ["As", "Kh"]}
        )
        print(f"  ✓ Success for allowed_user: {result['recommendation']}")
    except PermissionError as e:
        print(f"  ✗ Denied: {e}")

    # This should fail
    try:
        result = protected_function(
            user_id="denied_user",
            hand_data={"cards": ["As", "Kh"]}
        )
        print(f"  ✓ Success for denied_user: {result['recommendation']}")
    except PermissionError as e:
        print(f"  ✗ Denied for denied_user: {e}")


def example_security_scenarios():
    """Example 8: Real-world security scenarios."""
    print("\n=== Example 8: Security Scenarios ===\n")

    rbac = get_rbac_system()

    # Scenario 1: Privilege escalation prevention
    print("Scenario 1: Privilege Escalation Prevention")

    rbac.assign_role("regular_user", Role.USER)

    can_delete_users = rbac.has_permission("regular_user", Permission.DELETE_USER)
    can_manage_system = rbac.has_permission("regular_user", Permission.MANAGE_SYSTEM)

    print(f"  Regular user can delete users: {can_delete_users} ✓")
    print(f"  Regular user can manage system: {can_manage_system} ✓")

    # Scenario 2: Feature-based access control
    print("\nScenario 2: Feature-Based Access Control")

    # Free tier
    rbac.assign_role("free_user", Role.GUEST)
    can_use_gto = rbac.has_permission("free_user", Permission.USE_GTO_SOLVER)
    print(f"  Free tier can use GTO solver: {can_use_gto} ✓")

    # Premium tier
    rbac.assign_role("premium_user", Role.USER)
    can_use_gto = rbac.has_permission("premium_user", Permission.USE_GTO_SOLVER)
    print(f"  Premium tier can use GTO solver: {can_use_gto} ✓")

    # Scenario 3: Role revocation
    print("\nScenario 3: Role Revocation")

    rbac.assign_role("temp_admin", Role.ADMIN)
    print(f"  User is admin: {rbac.has_role('temp_admin', Role.ADMIN)}")

    rbac.revoke_role("temp_admin", Role.ADMIN)
    print(f"  After revocation, user is admin: {rbac.has_role('temp_admin', Role.ADMIN)} ✓")


def main():
    """Run all examples."""
    print("=" * 70)
    print("PokerTool RBAC System - Usage Examples")
    print("=" * 70)

    examples = [
        ("Basic Setup", example_basic_setup),
        ("Permission Checking", example_permission_checking),
        ("Role Hierarchy", example_role_hierarchy),
        ("Custom Roles", example_custom_roles),
        ("Multiple Roles", example_multiple_roles),
        ("Permission Groups", example_permission_groups),
        ("Function Decorators", example_function_decorators),
        ("Security Scenarios", example_security_scenarios)
    ]

    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n✗ Example '{name}' failed: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
