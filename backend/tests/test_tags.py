from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    Account,
    AccountSide,
    AccountStatus,
    AccountTag,
    Currency,
    Institution,
)


def test_list_tags_empty(client: TestClient) -> None:
    response = client.get("/tags")
    assert response.status_code == 200
    assert response.json() == []


def test_create_tag(client: TestClient) -> None:
    response = client.post("/tags", json={"name": "retirement"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "retirement"
    assert isinstance(body["id"], int)


def test_create_tag_duplicate(client: TestClient) -> None:
    client.post("/tags", json={"name": "retirement"})
    assert client.post("/tags", json={"name": "retirement"}).status_code == 409


def test_get_tag(client: TestClient) -> None:
    tag_id = client.post("/tags", json={"name": "savings"}).json()["id"]
    response = client.get(f"/tags/{tag_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "savings"


def test_get_tag_not_found(client: TestClient) -> None:
    assert client.get("/tags/9999").status_code == 404


def test_update_tag(client: TestClient) -> None:
    tag_id = client.post("/tags", json={"name": "old-name"}).json()["id"]
    response = client.put(f"/tags/{tag_id}", json={"name": "new-name"})
    assert response.status_code == 200
    assert response.json()["name"] == "new-name"


def test_update_tag_not_found(client: TestClient) -> None:
    assert client.put("/tags/9999", json={"name": "x"}).status_code == 404


def test_update_tag_duplicate_name(client: TestClient) -> None:
    client.post("/tags", json={"name": "alpha"})
    tag_id = client.post("/tags", json={"name": "beta"}).json()["id"]
    assert client.put(f"/tags/{tag_id}", json={"name": "alpha"}).status_code == 409


def test_delete_tag(client: TestClient) -> None:
    tag_id = client.post("/tags", json={"name": "temp"}).json()["id"]
    assert client.delete(f"/tags/{tag_id}").status_code == 204
    assert client.get(f"/tags/{tag_id}").status_code == 404


def test_delete_tag_clears_account_tag(client: TestClient, session: Session) -> None:
    # Seed dependencies directly via session
    currency = Currency(code="USD", name="US Dollar")
    institution = Institution(name="Test Bank")
    session.add_all([currency, institution])
    session.commit()
    session.refresh(institution)
    assert institution.id is not None

    account = Account(
        name="Test Account",
        institution_id=institution.id,
        currency_code="USD",
        side=AccountSide.asset,
        status=AccountStatus.active,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    assert account.id is not None

    tag_id = client.post("/tags", json={"name": "to-delete"}).json()["id"]
    session.add(AccountTag(account_id=account.id, tag_id=tag_id))
    session.commit()

    assert client.delete(f"/tags/{tag_id}").status_code == 204

    # Tag is gone
    assert client.get(f"/tags/{tag_id}").status_code == 404

    # Account still exists
    remaining = session.exec(select(Account).where(Account.id == account.id)).first()
    assert remaining is not None

    # AccountTag row is gone
    join_row = session.exec(
        select(AccountTag).where(AccountTag.tag_id == tag_id)
    ).first()
    assert join_row is None


def test_delete_tag_not_found(client: TestClient) -> None:
    assert client.delete("/tags/9999").status_code == 404
