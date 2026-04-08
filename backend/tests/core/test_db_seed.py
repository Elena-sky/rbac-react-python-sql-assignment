from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.core.db import init_db
from app.models import User, UserRole, UserUpdate


def test_init_db_seeds_required_role_users(db: Session) -> None:
    init_db(db)

    admin_user = crud.get_user_by_email(session=db, email=str(settings.FIRST_SUPERUSER))
    manager_user = crud.get_user_by_email(session=db, email=str(settings.MANAGER_USER_EMAIL))
    member_user = crud.get_user_by_email(session=db, email=str(settings.MEMBER_USER_EMAIL))

    assert admin_user is not None
    assert manager_user is not None
    assert member_user is not None
    assert admin_user.role == UserRole.ADMIN
    assert manager_user.role == UserRole.MANAGER
    assert member_user.role == UserRole.MEMBER
    assert admin_user.is_superuser is True
    assert manager_user.is_superuser is False
    assert member_user.is_superuser is False


def test_init_db_is_idempotent_for_seed_users(db: Session) -> None:
    seed_emails = [
        str(settings.FIRST_SUPERUSER),
        str(settings.MANAGER_USER_EMAIL),
        str(settings.MEMBER_USER_EMAIL),
    ]
    count_before = len(
        db.exec(select(User).where(User.email.in_(seed_emails))).all()
    )

    init_db(db)
    init_db(db)

    count_after = len(db.exec(select(User).where(User.email.in_(seed_emails))).all())
    assert count_before == count_after


def test_init_db_does_not_override_existing_seed_user_password(db: Session) -> None:
    manager_user = crud.get_user_by_email(session=db, email=str(settings.MANAGER_USER_EMAIL))
    assert manager_user is not None

    manager_user = crud.update_user(
        session=db,
        db_user=manager_user,
        user_in=UserUpdate(password="changed-manager-password"),
    )
    hashed_password_before = manager_user.hashed_password

    init_db(db)

    refreshed_manager = crud.get_user_by_email(
        session=db, email=str(settings.MANAGER_USER_EMAIL)
    )
    assert refreshed_manager is not None
    assert refreshed_manager.hashed_password == hashed_password_before
    assert refreshed_manager.role == UserRole.MANAGER
    assert refreshed_manager.is_superuser is False
