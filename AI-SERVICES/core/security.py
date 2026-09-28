import os
from pathlib import Path
from typing import List, Optional
from fastapi import HTTPException, status
from core.config import settings

ALLOWED_ROLES = ["admin", "operator", "engineer", "analyst", "viewer"]

ADMIN_ONLY_ACTIONS = [
    "register_model",
    "modify_model",
    "delete_model",
    "configure_agent",
    "system_config",
    "manage_users"
]

def validate_safe_path(target_path: str, allowed_dirs: Optional[List[Path]] = None) -> Path:
    """
    Prevent directory traversal attacks by verifying that target_path
    resolves strictly within designated storage boundaries.
    """
    if allowed_dirs is None:
        allowed_dirs = [
            settings.STORAGE_DIR,
            settings.UPLOAD_DIR,
            settings.ARTIFACT_DIR,
            settings.TEMP_DIR,
            settings.BASE_DIR
        ]
        
    resolved = Path(target_path).resolve()
    
    # Check if resolved path starts with any allowed directory
    is_safe = False
    for allowed in allowed_dirs:
        try:
            resolved.relative_to(allowed.resolve())
            is_safe = True
            break
        except ValueError:
            continue
            
    if not is_safe:
        raise PermissionError(f"Directory traversal detected: access to '{target_path}' is denied.")
        
    return resolved

def verify_rbac_permission(user_role: str, action: str) -> bool:
    """
    Enforce sovereign RBAC policy:
    - admin: all actions
    - operator, engineer: execution, documents, tasks
    - analyst: reading, reports, inspection
    - viewer: read-only
    """
    normalized_role = user_role.lower().strip()
    if normalized_role not in ALLOWED_ROLES:
        return False
        
    if action in ADMIN_ONLY_ACTIONS:
        return normalized_role == "admin"
        
    if normalized_role == "viewer" and not action.startswith("view_") and not action.startswith("read_"):
        return False
        
    return True
