from typing import List
from ..models.user import UserRole

# Define permissions for each role
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: [
        "manage_users",
        "manage_employees",
        "manage_projects",
        "manage_tasks",
        "manage_blogs",
        "manage_settings",
        "view_all_attendance",
        "manage_attendance"
    ],
    UserRole.ADMIN: [
        "manage_employees",
        "manage_projects",
        "manage_tasks",
        "manage_blogs",
        "view_all_attendance",
        "manage_attendance"
    ],
    UserRole.PROJECT_MANAGER: [
        "create_projects",
        "manage_own_projects",
        "create_tasks",
        "manage_tasks",
        "view_team_attendance"
    ],
    UserRole.EMPLOYEE: [
        "view_own_tasks",
        "update_own_tasks",
        "mark_attendance",
        "view_own_attendance"
    ],
    UserRole.CONTENT_EDITOR: [
        "create_blogs",
        "edit_own_blogs",
        "view_blogs"
    ]
}

def has_permission(user_role: UserRole, permission: str) -> bool:
    """Check if a role has a specific permission"""
    return permission in ROLE_PERMISSIONS.get(user_role, [])

def get_user_permissions(user_role: UserRole) -> List[str]:
    """Get all permissions for a user role"""
    return ROLE_PERMISSIONS.get(user_role, [])