import uuid

import pytest
from fastapi import HTTPException, Request

from app.api.authz import (
    get_effective_role,
    require_admin,
    require_owner_or_admin,
    require_admin_or_manager,
    require_non_admin,
    require_not_self,
    require_roles,
    require_self_or_admin,
)
from app.models import User, UserRole


def make_user(*, role: UserRole, is_superuser: bool = False) -> User:
    return User(
        id=uuid.uuid4(),
        email=f"{uuid.uuid4()}@example.com",
        hashed_password="x",
        role=role,
        is_superuser=is_superuser,
    )


def make_request(path_params: dict[str, str]) -> Request:
    return Request({"type": "http", "path_params": path_params})


def test_get_effective_role_maps_superuser_to_admin() -> None:
    user = make_user(role=UserRole.MEMBER, is_superuser=True)
    assert get_effective_role(user) == UserRole.ADMIN


def test_require_roles_denies_with_403() -> None:
    dependency = require_roles(UserRole.ADMIN)
    user = make_user(role=UserRole.MEMBER)
    with pytest.raises(HTTPException) as exc_info:
        dependency(user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"


def test_require_admin_or_manager_allows_manager() -> None:
    dependency = require_admin_or_manager()
    manager = make_user(role=UserRole.MANAGER)
    dependency(manager)


def test_require_admin_allows_admin() -> None:
    dependency = require_admin()
    admin = make_user(role=UserRole.ADMIN)
    dependency(admin)


def test_require_admin_denies_non_admin() -> None:
    dependency = require_admin()
    manager = make_user(role=UserRole.MANAGER)
    with pytest.raises(HTTPException) as exc_info:
        dependency(manager)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"


def test_require_self_or_admin_allows_self() -> None:
    dependency = require_self_or_admin("user_id")
    user = make_user(role=UserRole.MEMBER)
    request = make_request({"user_id": str(user.id)})
    dependency(request, user)


def test_require_self_or_admin_allows_admin_bypass() -> None:
    dependency = require_self_or_admin("user_id")
    admin = make_user(role=UserRole.ADMIN)
    request = make_request({"user_id": str(uuid.uuid4())})
    dependency(request, admin)


def test_require_self_or_admin_denies_with_403() -> None:
    dependency = require_self_or_admin("user_id")
    user = make_user(role=UserRole.MEMBER)
    request = make_request({"user_id": str(uuid.uuid4())})
    with pytest.raises(HTTPException) as exc_info:
        dependency(request, user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"


def test_require_self_or_admin_missing_path_param_denies_with_403() -> None:
    dependency = require_self_or_admin("user_id")
    user = make_user(role=UserRole.MEMBER)
    request = make_request({})
    with pytest.raises(HTTPException) as exc_info:
        dependency(request, user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"


def test_require_non_admin_denies_admin_with_403() -> None:
    dependency = require_non_admin()
    admin = make_user(role=UserRole.ADMIN)
    with pytest.raises(HTTPException) as exc_info:
        dependency(admin)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Super users are not allowed to delete themselves"


def test_require_non_admin_allows_member() -> None:
    dependency = require_non_admin()
    member = make_user(role=UserRole.MEMBER)
    dependency(member)


def test_require_not_self_denies_self_with_403() -> None:
    dependency = require_not_self("user_id")
    user = make_user(role=UserRole.ADMIN)
    request = make_request({"user_id": str(user.id)})
    with pytest.raises(HTTPException) as exc_info:
        dependency(request, user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Super users are not allowed to delete themselves"


def test_require_not_self_allows_non_self() -> None:
    dependency = require_not_self("user_id")
    user = make_user(role=UserRole.ADMIN)
    request = make_request({"user_id": str(uuid.uuid4())})
    dependency(request, user)


def test_require_not_self_missing_path_param_denies_with_403() -> None:
    dependency = require_not_self("user_id")
    user = make_user(role=UserRole.ADMIN)
    request = make_request({})
    with pytest.raises(HTTPException) as exc_info:
        dependency(request, user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"


def test_require_owner_or_admin_allows_owner() -> None:
    owner = make_user(role=UserRole.MEMBER)
    require_owner_or_admin(owner, owner.id)


def test_require_owner_or_admin_allows_admin() -> None:
    admin = make_user(role=UserRole.ADMIN)
    require_owner_or_admin(admin, uuid.uuid4())


def test_require_owner_or_admin_denies_foreign_non_admin() -> None:
    member = make_user(role=UserRole.MEMBER)
    with pytest.raises(HTTPException) as exc_info:
        require_owner_or_admin(member, uuid.uuid4())
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"
