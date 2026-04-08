from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, UserRole, UserUpdate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def _seed_user(
    *,
    session: Session,
    email: str,
    password: str,
    role: UserRole,
    is_superuser: bool,
) -> str:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user_create = UserCreate(
            email=email,
            password=password,
            is_superuser=is_superuser,
            role=role,
        )
        crud.create_user(session=session, user_create=user_create)
        return "created"
    user_update = UserUpdate(role=role, is_superuser=is_superuser)
    crud.update_user(session=session, db_user=user, user_in=user_update)
    return "updated"


def init_db(session: Session) -> dict[str, str]:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    admin_result = _seed_user(
        session=session,
        email=str(settings.FIRST_SUPERUSER),
        password=settings.FIRST_SUPERUSER_PASSWORD,
        role=UserRole.ADMIN,
        is_superuser=True,
    )
    manager_result = _seed_user(
        session=session,
        email=str(settings.MANAGER_USER_EMAIL),
        password=settings.MANAGER_USER_PASSWORD,
        role=UserRole.MANAGER,
        is_superuser=False,
    )
    member_result = _seed_user(
        session=session,
        email=str(settings.MEMBER_USER_EMAIL),
        password=settings.MEMBER_USER_PASSWORD,
        role=UserRole.MEMBER,
        is_superuser=False,
    )
    return {
        "admin": admin_result,
        "manager": manager_result,
        "member": member_result,
    }
