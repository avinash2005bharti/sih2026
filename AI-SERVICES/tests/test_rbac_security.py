import pytest
from core.security import verify_rbac_permission, ALLOWED_ROLES

def test_rbac_roles_valid():
    assert "admin" in ALLOWED_ROLES
    assert "operator" in ALLOWED_ROLES
    assert "engineer" in ALLOWED_ROLES
    assert "analyst" in ALLOWED_ROLES
    assert "viewer" in ALLOWED_ROLES

def test_admin_permissions():
    assert verify_rbac_permission("admin", "register_model") is True
    assert verify_rbac_permission("admin", "modify_model") is True
    assert verify_rbac_permission("admin", "execute_python_executor") is True

def test_non_admin_denied_model_operations():
    assert verify_rbac_permission("operator", "register_model") is False
    assert verify_rbac_permission("engineer", "register_model") is False
    assert verify_rbac_permission("analyst", "register_model") is False
    assert verify_rbac_permission("viewer", "register_model") is False

def test_viewer_read_only():
    assert verify_rbac_permission("viewer", "view_document") is True
    assert verify_rbac_permission("viewer", "read_file") is True
    assert verify_rbac_permission("viewer", "execute_file_writer") is False
