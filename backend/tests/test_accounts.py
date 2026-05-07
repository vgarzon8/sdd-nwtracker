from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    AccountTag,
    Balance,
    Tag,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_currency(client: TestClient, code: str = "USD") -> None:
    client.post("/currencies", json={"code": code, "name": f"{code} Currency"})


def _make_institution(client: TestClient, name: str = "Bank A") -> int:
    return client.post("/institutions", json={"name": name}).json()["id"]


def _make_tag(client: TestClient, name: str = "retirement") -> int:
    return client.post("/tags", json={"name": name}).json()["id"]


def _make_account(client: TestClient, **overrides: object) -> dict:  # type: ignore[type-arg]
    defaults: dict = {  # type: ignore[type-arg]
        "name": "Checking",
        "institution_id": None,
        "currency_code": "USD",
        "side": "asset",
        "status": "active",
        "tag_ids": [],
    }
    defaults.update(overrides)
    return client.post("/accounts", json=defaults).json()


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_accounts_empty(client: TestClient) -> None:
    assert client.get("/accounts").status_code == 200
    assert client.get("/accounts").json() == []


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_account(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    response = client.post(
        "/accounts",
        json={
            "name": "Savings",
            "institution_id": inst_id,
            "currency_code": "USD",
            "side": "asset",
            "status": "active",
            "tag_ids": [],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Savings"
    assert body["institution_id"] == inst_id
    assert body["currency_code"] == "USD"
    assert body["side"] == "asset"
    assert body["status"] == "active"
    assert body["tag_ids"] == []
    assert isinstance(body["id"], int)


def test_create_account_default_status(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    response = client.post(
        "/accounts",
        json={
            "name": "Checking",
            "institution_id": inst_id,
            "currency_code": "USD",
            "side": "asset",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "active"


def test_create_account_duplicate_name(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    payload = {
        "name": "Checking",
        "institution_id": inst_id,
        "currency_code": "USD",
        "side": "asset",
    }
    client.post("/accounts", json=payload)
    assert client.post("/accounts", json=payload).status_code == 409


def test_create_account_invalid_institution(client: TestClient) -> None:
    _make_currency(client)
    response = client.post(
        "/accounts",
        json={
            "name": "Checking",
            "institution_id": 9999,
            "currency_code": "USD",
            "side": "asset",
        },
    )
    assert response.status_code == 404


def test_create_account_invalid_currency(client: TestClient) -> None:
    inst_id = _make_institution(client)
    response = client.post(
        "/accounts",
        json={
            "name": "Checking",
            "institution_id": inst_id,
            "currency_code": "XXX",
            "side": "asset",
        },
    )
    assert response.status_code == 404


def test_create_account_with_tags(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    tag_id = _make_tag(client)
    response = client.post(
        "/accounts",
        json={
            "name": "Tagged",
            "institution_id": inst_id,
            "currency_code": "USD",
            "side": "asset",
            "tag_ids": [tag_id],
        },
    )
    assert response.status_code == 201
    assert response.json()["tag_ids"] == [tag_id]


def test_create_account_invalid_tag(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    response = client.post(
        "/accounts",
        json={
            "name": "Bad Tag",
            "institution_id": inst_id,
            "currency_code": "USD",
            "side": "asset",
            "tag_ids": [9999],
        },
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


def test_get_account(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    acct_id = _make_account(client, institution_id=inst_id)["id"]
    response = client.get(f"/accounts/{acct_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == acct_id
    assert body["name"] == "Checking"


def test_get_account_not_found(client: TestClient) -> None:
    assert client.get("/accounts/9999").status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_account_name(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    acct_id = _make_account(client, institution_id=inst_id)["id"]
    response = client.put(f"/accounts/{acct_id}", json={"name": "Premium Savings"})
    assert response.status_code == 200
    assert response.json()["name"] == "Premium Savings"
    # other fields unchanged
    assert response.json()["side"] == "asset"


def test_update_account_status(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    acct_id = _make_account(client, institution_id=inst_id)["id"]
    response = client.put(f"/accounts/{acct_id}", json={"status": "closed"})
    assert response.status_code == 200
    assert response.json()["status"] == "closed"
    assert response.json()["name"] == "Checking"


def test_update_account_tags_replace(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    tag1_id = _make_tag(client, "tag1")
    tag2_id = _make_tag(client, "tag2")
    acct_id = _make_account(client, institution_id=inst_id, tag_ids=[tag1_id])["id"]

    response = client.put(f"/accounts/{acct_id}", json={"tag_ids": [tag2_id]})
    assert response.status_code == 200
    assert response.json()["tag_ids"] == [tag2_id]


def test_update_account_tags_none_leaves_unchanged(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    tag_id = _make_tag(client)
    acct_id = _make_account(client, institution_id=inst_id, tag_ids=[tag_id])["id"]

    # PUT without tag_ids field — tags must not change
    response = client.put(f"/accounts/{acct_id}", json={"status": "closed"})
    assert response.status_code == 200
    assert response.json()["tag_ids"] == [tag_id]


def test_update_account_not_found(client: TestClient) -> None:
    assert client.put("/accounts/9999", json={"name": "x"}).status_code == 404


def test_update_account_duplicate_name(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    _make_account(client, name="Alpha", institution_id=inst_id)
    acct_id = _make_account(client, name="Beta", institution_id=inst_id)["id"]
    assert client.put(f"/accounts/{acct_id}", json={"name": "Alpha"}).status_code == 409


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_list_filter_by_status(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    active_id = _make_account(client, name="Active", institution_id=inst_id)["id"]
    closed_id = _make_account(
        client, name="Closed", institution_id=inst_id, status="closed"
    )["id"]

    active_results = client.get("/accounts?status=active").json()
    assert any(a["id"] == active_id for a in active_results)
    assert all(a["id"] != closed_id for a in active_results)

    closed_results = client.get("/accounts?status=closed").json()
    assert any(a["id"] == closed_id for a in closed_results)
    assert all(a["id"] != active_id for a in closed_results)


def test_list_filter_by_tag(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    tag_id = _make_tag(client)
    tagged_id = _make_account(
        client, name="Tagged", institution_id=inst_id, tag_ids=[tag_id]
    )["id"]
    untagged_id = _make_account(client, name="Untagged", institution_id=inst_id)["id"]

    results = client.get(f"/accounts?tag={tag_id}").json()
    assert any(a["id"] == tagged_id for a in results)
    assert all(a["id"] != untagged_id for a in results)


def test_list_filter_status_and_tag(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    tag_id = _make_tag(client)

    match_id = _make_account(
        client, name="Match", institution_id=inst_id, tag_ids=[tag_id]
    )["id"]
    _make_account(
        client,
        name="Wrong Status",
        institution_id=inst_id,
        status="closed",
        tag_ids=[tag_id],
    )
    _make_account(client, name="No Tag", institution_id=inst_id)

    results = client.get(f"/accounts?status=active&tag={tag_id}").json()
    assert len(results) == 1
    assert results[0]["id"] == match_id


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_account_dry_run_no_balances(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    acct_id = _make_account(client, institution_id=inst_id)["id"]

    response = client.delete(f"/accounts/{acct_id}")
    assert response.status_code == 200
    assert response.json() == {"balances_to_delete": 0}
    # account still exists
    assert client.get(f"/accounts/{acct_id}").status_code == 200


def test_delete_account_dry_run_with_balances(
    client: TestClient, session: Session
) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    acct_id = _make_account(client, institution_id=inst_id)["id"]
    session.add(Balance(account_id=acct_id, month="2026-03", amount=500))
    session.add(Balance(account_id=acct_id, month="2026-04", amount=600))
    session.commit()

    response = client.delete(f"/accounts/{acct_id}")
    assert response.status_code == 200
    assert response.json()["balances_to_delete"] == 2


def test_delete_account_confirm(client: TestClient, session: Session) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    tag_id = _make_tag(client)
    acct_id = _make_account(
        client, name="Doomed", institution_id=inst_id, tag_ids=[tag_id]
    )["id"]
    session.add(Balance(account_id=acct_id, month="2026-04", amount=1000))
    session.commit()

    response = client.delete(f"/accounts/{acct_id}?confirm=true")
    assert response.status_code == 204

    # Account gone
    assert client.get(f"/accounts/{acct_id}").status_code == 404

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


def test_delete_account_confirm_leaves_tag(
    client: TestClient, session: Session
) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    tag_id = _make_tag(client, "survivor")
    acct_id = _make_account(
        client, name="Removed", institution_id=inst_id, tag_ids=[tag_id]
    )["id"]

    client.delete(f"/accounts/{acct_id}?confirm=true")

    # Tag itself still exists
    assert session.get(Tag, tag_id) is not None


def test_delete_account_not_found(client: TestClient) -> None:
    assert client.delete("/accounts/9999").status_code == 404
    assert client.delete("/accounts/9999?confirm=true").status_code == 404
