from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    Account,
    AccountSide,
    AccountStatus,
    AccountTag,
    Balance,
    Currency,
    Tag,
)


def _seed_account(session: Session, institution_id: int, name: str = "Acct") -> int:
    """Create a USD currency + account, return account id."""
    if not session.get(Currency, "USD"):
        session.add(Currency(code="USD", name="US Dollar"))
        session.commit()
    account = Account(
        name=name,
        institution_id=institution_id,
        currency_code="USD",
        side=AccountSide.asset,
        status=AccountStatus.active,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    assert account.id is not None
    return account.id


def test_list_institutions_empty(client: TestClient) -> None:
    assert client.get("/institutions").status_code == 200
    assert client.get("/institutions").json() == []


def test_create_institution(client: TestClient) -> None:
    response = client.post("/institutions", json={"name": "Chase"})
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Chase"
    assert isinstance(body["id"], int)


def test_create_institution_duplicate(client: TestClient) -> None:
    client.post("/institutions", json={"name": "Chase"})
    assert client.post("/institutions", json={"name": "Chase"}).status_code == 409


def test_get_institution(client: TestClient) -> None:
    inst_id = client.post("/institutions", json={"name": "Chase"}).json()["id"]
    response = client.get(f"/institutions/{inst_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Chase"


def test_get_institution_not_found(client: TestClient) -> None:
    assert client.get("/institutions/9999").status_code == 404


def test_update_institution(client: TestClient) -> None:
    inst_id = client.post("/institutions", json={"name": "Old Bank"}).json()["id"]
    response = client.put(f"/institutions/{inst_id}", json={"name": "New Bank"})
    assert response.status_code == 200
    assert response.json()["name"] == "New Bank"


def test_update_institution_not_found(client: TestClient) -> None:
    assert client.put("/institutions/9999", json={"name": "x"}).status_code == 404


def test_update_institution_duplicate_name(client: TestClient) -> None:
    client.post("/institutions", json={"name": "Alpha"})
    inst_id = client.post("/institutions", json={"name": "Beta"}).json()["id"]
    assert (
        client.put(f"/institutions/{inst_id}", json={"name": "Alpha"}).status_code
        == 409
    )


def test_delete_institution_dry_run_no_accounts(client: TestClient) -> None:
    inst_id = client.post("/institutions", json={"name": "Empty Bank"}).json()["id"]
    response = client.delete(f"/institutions/{inst_id}")
    assert response.status_code == 200
    body = response.json()
    assert body == {"accounts_to_delete": 0, "balances_to_delete": 0}


def test_delete_institution_dry_run_with_accounts(
    client: TestClient, session: Session
) -> None:
    inst_id = client.post("/institutions", json={"name": "Big Bank"}).json()["id"]
    acct_id = _seed_account(session, inst_id, "Account A")
    session.add(Balance(account_id=acct_id, month="2026-04", amount=1000))
    session.add(Balance(account_id=acct_id, month="2026-05", amount=1100))
    session.commit()

    response = client.delete(f"/institutions/{inst_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["accounts_to_delete"] == 1
    assert body["balances_to_delete"] == 2


def test_delete_institution_dry_run_no_data_modified(
    client: TestClient, session: Session
) -> None:
    inst_id = client.post("/institutions", json={"name": "Safe Bank"}).json()["id"]
    _seed_account(session, inst_id)

    client.delete(f"/institutions/{inst_id}")

    # Institution still exists
    assert client.get(f"/institutions/{inst_id}").status_code == 200


def test_delete_institution_confirm(client: TestClient, session: Session) -> None:
    inst_id = client.post("/institutions", json={"name": "Doomed Bank"}).json()["id"]
    acct_id = _seed_account(session, inst_id)

    tag = Tag(name="test-tag")
    session.add(tag)
    session.commit()
    session.refresh(tag)
    assert tag.id is not None
    session.add(AccountTag(account_id=acct_id, tag_id=tag.id))
    session.add(Balance(account_id=acct_id, month="2026-04", amount=500))
    session.commit()

    response = client.delete(f"/institutions/{inst_id}?confirm=true")
    assert response.status_code == 204

    # Institution gone
    assert client.get(f"/institutions/{inst_id}").status_code == 404

    # Account gone
    assert session.exec(select(Account).where(Account.id == acct_id)).first() is None

    # Balances gone
    assert (
        session.exec(select(Balance).where(Balance.account_id == acct_id)).first()
        is None
    )

    # AccountTag rows gone
    assert (
        session.exec(select(AccountTag).where(AccountTag.account_id == acct_id)).first()
        is None
    )


def test_delete_institution_not_found(client: TestClient) -> None:
    assert client.delete("/institutions/9999").status_code == 404
    assert client.delete("/institutions/9999?confirm=true").status_code == 404
