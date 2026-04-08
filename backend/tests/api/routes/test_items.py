import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from tests.utils.item import create_random_item
from tests.utils.user import manager_token_headers


def create_item_as_user(
    client: TestClient, headers: dict[str, str], *, title: str = "Owned item"
) -> dict:
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=headers,
        json={"title": title, "description": "Owned description"},
    )
    assert response.status_code == 200
    return response.json()


def current_user_id(client: TestClient, headers: dict[str, str]) -> str:
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert response.status_code == 200
    return response.json()["id"]


def test_create_item(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Foo", "description": "Fighters"}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content


def test_read_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_read_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Forbidden"


def test_read_item_as_member_owner_allowed(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    created_item = create_item_as_user(client, normal_user_token_headers, title="Member own")
    response = client.get(
        f"{settings.API_V1_STR}/items/{created_item['id']}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == created_item["id"]


def test_read_item_as_manager_owner_allowed(client: TestClient, db: Session) -> None:
    manager_headers = manager_token_headers(client=client, db=db)
    created_item = create_item_as_user(client, manager_headers, title="Manager own")
    response = client.get(
        f"{settings.API_V1_STR}/items/{created_item['id']}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["id"] == created_item["id"]


def test_read_item_as_manager_foreign_forbidden(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    manager_headers = manager_token_headers(client=client, db=db)
    member_item = create_item_as_user(client, normal_user_token_headers, title="Member item")
    response = client.get(
        f"{settings.API_V1_STR}/items/{member_item['id']}",
        headers=manager_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_read_items(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    create_random_item(db)
    create_random_item(db)
    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content["data"]) >= 2


def test_read_items_as_member_returns_only_own(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    create_random_item(db)
    own_item = create_item_as_user(client, normal_user_token_headers, title="Visible only mine")
    member_id = current_user_id(client, normal_user_token_headers)

    response = client.get(f"{settings.API_V1_STR}/items/", headers=normal_user_token_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["count"] >= 1
    assert any(item["id"] == own_item["id"] for item in content["data"])
    assert all(item["owner_id"] == member_id for item in content["data"])


def test_read_items_as_manager_returns_only_own(client: TestClient, db: Session) -> None:
    manager_headers = manager_token_headers(client=client, db=db)
    create_random_item(db)
    own_item = create_item_as_user(client, manager_headers, title="Manager visible own")
    manager_id = current_user_id(client, manager_headers)

    response = client.get(f"{settings.API_V1_STR}/items/", headers=manager_headers)
    assert response.status_code == 200
    content = response.json()
    assert content["count"] >= 1
    assert any(item["id"] == own_item["id"] for item in content["data"])
    assert all(item["owner_id"] == manager_id for item in content["data"])


def test_update_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_update_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_update_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Forbidden"


def test_update_item_as_member_owner_allowed(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    created_item = create_item_as_user(client, normal_user_token_headers, title="Before update")
    response = client.put(
        f"{settings.API_V1_STR}/items/{created_item['id']}",
        headers=normal_user_token_headers,
        json={"title": "After update", "description": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "After update"


def test_update_item_as_manager_owner_allowed(client: TestClient, db: Session) -> None:
    manager_headers = manager_token_headers(client=client, db=db)
    created_item = create_item_as_user(client, manager_headers, title="Manager before")
    response = client.put(
        f"{settings.API_V1_STR}/items/{created_item['id']}",
        headers=manager_headers,
        json={"title": "Manager after", "description": "Updated"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Manager after"


def test_update_item_as_manager_foreign_forbidden(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    manager_headers = manager_token_headers(client=client, db=db)
    member_item = create_item_as_user(client, normal_user_token_headers, title="Member foreign")
    response = client.put(
        f"{settings.API_V1_STR}/items/{member_item['id']}",
        headers=manager_headers,
        json={"title": "Should fail", "description": "Nope"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_delete_item(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Item deleted successfully"


def test_delete_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    item = create_random_item(db)
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    content = response.json()
    assert content["detail"] == "Forbidden"


def test_delete_item_as_member_owner_allowed(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    created_item = create_item_as_user(client, normal_user_token_headers, title="Delete mine")
    response = client.delete(
        f"{settings.API_V1_STR}/items/{created_item['id']}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"


def test_delete_item_as_manager_owner_allowed(client: TestClient, db: Session) -> None:
    manager_headers = manager_token_headers(client=client, db=db)
    created_item = create_item_as_user(client, manager_headers, title="Delete manager own")
    response = client.delete(
        f"{settings.API_V1_STR}/items/{created_item['id']}",
        headers=manager_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"


def test_delete_item_as_manager_foreign_forbidden(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    manager_headers = manager_token_headers(client=client, db=db)
    member_item = create_item_as_user(client, normal_user_token_headers, title="Member protected")
    response = client.delete(
        f"{settings.API_V1_STR}/items/{member_item['id']}",
        headers=manager_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"


def test_create_item_as_member_allowed(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
        json={"title": "Member create", "description": "Allowed"},
    )
    assert response.status_code == 200


def test_create_item_as_manager_allowed(client: TestClient, db: Session) -> None:
    manager_headers = manager_token_headers(client=client, db=db)
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=manager_headers,
        json={"title": "Manager create", "description": "Allowed"},
    )
    assert response.status_code == 200


def test_items_routes_unauthenticated_return_401(client: TestClient) -> None:
    item_id = uuid.uuid4()
    list_response = client.get(f"{settings.API_V1_STR}/items/")
    read_response = client.get(f"{settings.API_V1_STR}/items/{item_id}")
    create_response = client.post(
        f"{settings.API_V1_STR}/items/",
        json={"title": "No auth", "description": "Denied"},
    )
    update_response = client.put(
        f"{settings.API_V1_STR}/items/{item_id}",
        json={"title": "No auth", "description": "Denied"},
    )
    delete_response = client.delete(f"{settings.API_V1_STR}/items/{item_id}")

    assert list_response.status_code == 401
    assert read_response.status_code == 401
    assert create_response.status_code == 401
    assert update_response.status_code == 401
    assert delete_response.status_code == 401
