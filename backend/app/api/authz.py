import uuid
from collections.abc import Callable

from fastapi import HTTPException, Request, status

from app.api.deps import CurrentUser
from app.models import User, UserRole


def _raise_forbidden() -> None:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def get_effective_role(user: User) -> UserRole:
    if user.is_superuser:
        return UserRole.ADMIN
    return user.role


def is_admin_user(user: User) -> bool:
    return get_effective_role(user) == UserRole.ADMIN


def require_roles(*allowed_roles: UserRole) -> Callable:
    def dependency(current_user: CurrentUser) -> None:
        if get_effective_role(current_user) not in allowed_roles:
            _raise_forbidden()

    return dependency


def require_admin() -> Callable:
    return require_roles(UserRole.ADMIN)


def require_admin_or_manager() -> Callable:
    return require_roles(UserRole.ADMIN, UserRole.MANAGER)


def require_self_or_admin(user_id_param: str) -> Callable:
    def dependency(
        request: Request,
        current_user: CurrentUser,
    ) -> None:
        if is_admin_user(current_user):
            return
        target_user_id = request.path_params.get(user_id_param)
        if target_user_id is None:
            _raise_forbidden()
        if str(current_user.id) != str(target_user_id):
            _raise_forbidden()

    return dependency


def require_owner_or_admin(current_user: User, owner_id: uuid.UUID) -> None:
    if is_admin_user(current_user):
        return
    if current_user.id != owner_id:
        _raise_forbidden()
