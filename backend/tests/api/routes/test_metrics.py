from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import UserCreate, UserRole
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def manager_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    email = random_email()
    password = random_lower_string()
    manager_in = UserCreate(email=email, password=password, role=UserRole.MANAGER)
    crud.create_user(session=db, user_create=manager_in)
    return user_authentication_headers(client=client, email=email, password=password)


def test_get_metrics_as_admin(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    r = client.get(f"{settings.API_V1_STR}/metrics/", headers=superuser_token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "generated_at" in body
    assert body["summary"] == {
        "users_total": 0,
        "active_users": 0,
        "reports_generated_today": 0,
    }


def test_get_metrics_as_manager(client: TestClient, db: Session) -> None:
    headers = manager_token_headers(client, db)
    r = client.get(f"{settings.API_V1_STR}/metrics/", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "generated_at" in body


def test_get_metrics_as_member_forbidden(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    r = client.get(f"{settings.API_V1_STR}/metrics/", headers=normal_user_token_headers)
    assert r.status_code == 403
    assert r.json() == {"detail": "Forbidden"}


def test_get_metrics_unauthenticated(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/metrics/")
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"
