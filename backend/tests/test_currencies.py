from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Account, AccountSide, AccountStatus, Currency, Institution


def test_list_currencies_empty(client: TestClient) -> None:
    response = client.get("/currencies")
    assert response.status_code == 200
    assert response.json() == []


def test_create_currency(client: TestClient) -> None:
    response = client.post("/currencies", json={"code": "EUR", "name": "Euro"})
    assert response.status_code == 201
    body = response.json()
    assert body["code"] == "EUR"
    assert body["name"] == "Euro"


def test_create_currency_duplicate(client: TestClient) -> None:
    client.post("/currencies", json={"code": "EUR", "name": "Euro"})
    response = client.post("/currencies", json={"code": "EUR", "name": "Euro"})
    assert response.status_code == 409


def test_get_currency(client: TestClient) -> None:
    client.post("/currencies", json={"code": "USD", "name": "US Dollar"})
    response = client.get("/currencies/USD")
    assert response.status_code == 200
    assert response.json()["code"] == "USD"


def test_get_currency_not_found(client: TestClient) -> None:
    assert client.get("/currencies/ZZZ").status_code == 404


def test_delete_currency(client: TestClient) -> None:
    client.post("/currencies", json={"code": "EUR", "name": "Euro"})
    assert client.delete("/currencies/EUR").status_code == 204
    assert client.get("/currencies/EUR").status_code == 404


def test_delete_currency_blocked_by_account(
    client: TestClient, session: Session
) -> None:
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
    assert client.delete("/currencies/USD").status_code == 409


def test_delete_currency_not_found(client: TestClient) -> None:
    assert client.delete("/currencies/ZZZ").status_code == 404
