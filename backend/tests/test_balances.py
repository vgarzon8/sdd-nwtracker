from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_currency(client: TestClient, code: str = "USD") -> None:
    client.post("/currencies", json={"code": code, "name": f"{code} Currency"})


def _make_institution(client: TestClient, name: str = "Bank A") -> int:
    return client.post("/institutions", json={"name": name}).json()["id"]


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


def _make_balance(
    client: TestClient, account_id: int, month: str = "2026-03", amount: int = 1000
) -> dict:  # type: ignore[type-arg]
    return client.post(
        "/balances", json={"account_id": account_id, "month": month, "amount": amount}
    ).json()


def _setup(
    client: TestClient, account_name: str = "Checking", side: str = "asset"
) -> int:
    """Create currency + institution + account, return account_id."""
    _make_currency(client)
    inst_id = _make_institution(client)
    return _make_account(client, name=account_name, institution_id=inst_id, side=side)[
        "id"
    ]


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_balances_empty(client: TestClient) -> None:
    assert client.get("/balances").status_code == 200
    assert client.get("/balances").json() == []


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_balance(client: TestClient) -> None:
    acct_id = _setup(client)
    response = client.post(
        "/balances", json={"account_id": acct_id, "month": "2026-03", "amount": 5000}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["account_id"] == acct_id
    assert body["month"] == "2026-03"
    assert body["amount"] == 5000
    assert isinstance(body["id"], int)


def test_create_balance_duplicate(client: TestClient) -> None:
    acct_id = _setup(client)
    client.post(
        "/balances", json={"account_id": acct_id, "month": "2026-03", "amount": 100}
    )
    response = client.post(
        "/balances", json={"account_id": acct_id, "month": "2026-03", "amount": 200}
    )
    assert response.status_code == 409


def test_create_balance_invalid_account(client: TestClient) -> None:
    response = client.post(
        "/balances", json={"account_id": 9999, "month": "2026-03", "amount": 100}
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


def test_get_balance(client: TestClient) -> None:
    acct_id = _setup(client)
    bal_id = _make_balance(client, acct_id, "2026-03", 8000)["id"]
    response = client.get(f"/balances/{bal_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == bal_id
    assert body["amount"] == 8000
    assert body["account_name"] == "Checking"
    assert body["currency_code"] == "USD"
    assert body["side"] == "asset"
    assert isinstance(body["institution_id"], int)


def test_get_balance_not_found(client: TestClient) -> None:
    assert client.get("/balances/9999").status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_balance(client: TestClient) -> None:
    acct_id = _setup(client)
    bal_id = _make_balance(client, acct_id, "2026-03", 1000)["id"]
    response = client.put(f"/balances/{bal_id}", json={"amount": 2500})
    assert response.status_code == 200
    assert response.json()["amount"] == 2500
    assert client.get(f"/balances/{bal_id}").json()["amount"] == 2500


def test_update_balance_not_found(client: TestClient) -> None:
    assert client.put("/balances/9999", json={"amount": 100}).status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_balance(client: TestClient) -> None:
    acct_id = _setup(client)
    bal_id = _make_balance(client, acct_id)["id"]
    assert client.delete(f"/balances/{bal_id}").status_code == 204
    assert client.get(f"/balances/{bal_id}").status_code == 404


def test_delete_balance_not_found(client: TestClient) -> None:
    assert client.delete("/balances/9999").status_code == 404


# ---------------------------------------------------------------------------
# Month filter
# ---------------------------------------------------------------------------


def test_list_by_month(client: TestClient) -> None:
    acct_id = _setup(client)
    _make_balance(client, acct_id, "2026-03", 1000)
    _make_balance(client, acct_id, "2026-04", 2000)

    march = client.get("/balances?month=2026-03").json()
    assert len(march) == 1
    assert march[0]["month"] == "2026-03"
    assert march[0]["amount"] == 1000

    april = client.get("/balances?month=2026-04").json()
    assert len(april) == 1
    assert april[0]["amount"] == 2000


def test_list_by_month_includes_account_detail(client: TestClient) -> None:
    acct_id = _setup(client)
    _make_balance(client, acct_id, "2026-03", 500)

    items = client.get("/balances?month=2026-03").json()
    assert len(items) == 1
    item = items[0]
    assert item["account_name"] == "Checking"
    assert item["currency_code"] == "USD"
    assert item["side"] == "asset"
    assert isinstance(item["institution_id"], int)


# ---------------------------------------------------------------------------
# Roll-forward
# ---------------------------------------------------------------------------


def test_roll_forward_basic(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    acct1 = _make_account(client, name="A1", institution_id=inst_id)["id"]
    acct2 = _make_account(client, name="A2", institution_id=inst_id)["id"]
    _make_balance(client, acct1, "2026-03", 1000)
    _make_balance(client, acct2, "2026-03", 2000)

    response = client.post("/balances/roll-forward", json={"month": "2026-04"})
    assert response.status_code == 200
    months = response.json()["months"]
    assert len(months) == 1
    assert months[0]["month"] == "2026-04"
    assert months[0]["inserted"] == 2
    assert months[0]["skipped"] == 0

    april = client.get("/balances?month=2026-04").json()
    amounts = {item["account_id"]: item["amount"] for item in april}
    assert amounts[acct1] == 1000
    assert amounts[acct2] == 2000


def test_roll_forward_idempotent(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    acct_id = _make_account(client, name="Savings", institution_id=inst_id)["id"]
    _make_balance(client, acct_id, "2026-03", 5000)

    client.post("/balances/roll-forward", json={"month": "2026-04"})
    response = client.post("/balances/roll-forward", json={"month": "2026-04"})
    assert response.status_code == 200
    month_result = response.json()["months"][0]
    assert month_result["inserted"] == 0
    assert month_result["skipped"] == 1

    assert len(client.get("/balances?month=2026-04").json()) == 1


def test_roll_forward_skips_existing(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    acct1 = _make_account(client, name="A1", institution_id=inst_id)["id"]
    acct2 = _make_account(client, name="A2", institution_id=inst_id)["id"]
    _make_balance(client, acct1, "2026-03", 1000)
    _make_balance(client, acct2, "2026-03", 2000)
    # Pre-seed acct2 in target month
    _make_balance(client, acct2, "2026-04", 9999)

    response = client.post("/balances/roll-forward", json={"month": "2026-04"})
    assert response.status_code == 200
    month_result = response.json()["months"][0]
    assert month_result["inserted"] == 1
    assert month_result["skipped"] == 1

    # acct2's pre-existing balance should not be overwritten
    april = client.get("/balances?month=2026-04").json()
    amounts = {item["account_id"]: item["amount"] for item in april}
    assert amounts[acct2] == 9999


def test_roll_forward_excludes_closed_accounts(client: TestClient) -> None:
    _make_currency(client)
    inst_id = _make_institution(client)
    active = _make_account(
        client, name="Active", institution_id=inst_id, status="active"
    )["id"]
    closed = _make_account(
        client, name="Closed", institution_id=inst_id, status="closed"
    )["id"]
    _make_balance(client, active, "2026-03", 1000)
    _make_balance(client, closed, "2026-03", 5000)

    response = client.post("/balances/roll-forward", json={"month": "2026-04"})
    assert response.status_code == 200
    assert response.json()["months"][0]["inserted"] == 1

    april_ids = {
        item["account_id"] for item in client.get("/balances?month=2026-04").json()
    }
    assert active in april_ids
    assert closed not in april_ids


def test_roll_forward_no_balances(client: TestClient) -> None:
    _setup(client)  # account exists but no balances
    response = client.post("/balances/roll-forward", json={"month": "2026-04"})
    assert response.status_code == 422


def test_roll_forward_same_month(client: TestClient) -> None:
    acct_id = _setup(client)
    _make_balance(client, acct_id, "2026-03", 1000)

    response = client.post("/balances/roll-forward", json={"month": "2026-03"})
    assert response.status_code == 422


def test_roll_forward_cascade(client: TestClient) -> None:
    """Skipping months fills all intermediate months in order."""
    _make_currency(client)
    inst_id = _make_institution(client)
    acct1 = _make_account(client, name="A1", institution_id=inst_id)["id"]
    acct2 = _make_account(client, name="A2", institution_id=inst_id)["id"]
    _make_balance(client, acct1, "2026-01", 1000)
    _make_balance(client, acct2, "2026-01", 2000)

    response = client.post("/balances/roll-forward", json={"month": "2026-04"})
    assert response.status_code == 200
    months = response.json()["months"]
    assert [m["month"] for m in months] == ["2026-02", "2026-03", "2026-04"]
    assert all(m["inserted"] == 2 for m in months)
    assert all(m["skipped"] == 0 for m in months)

    # All intermediate months populated
    for month in ("2026-02", "2026-03", "2026-04"):
        items = client.get(f"/balances?month={month}").json()
        assert len(items) == 2

    # Each month carries forward the same amounts
    for month in ("2026-02", "2026-03", "2026-04"):
        items = client.get(f"/balances?month={month}").json()
        amounts = {item["account_id"]: item["amount"] for item in items}
        assert amounts[acct1] == 1000
        assert amounts[acct2] == 2000


# ---------------------------------------------------------------------------
# Transfer
# ---------------------------------------------------------------------------


def _setup_two_accounts(
    client: TestClient,
    from_side: str = "asset",
    to_side: str = "asset",
) -> tuple[int, int]:
    """Create shared currency+institution, two accounts, return (from_id, to_id)."""
    _make_currency(client)
    inst_id = _make_institution(client)
    from_id = _make_account(
        client, name="From", institution_id=inst_id, side=from_side
    )["id"]
    to_id = _make_account(client, name="To", institution_id=inst_id, side=to_side)["id"]
    return from_id, to_id


def test_transfer_asset_to_asset(client: TestClient) -> None:
    from_id, to_id = _setup_two_accounts(client, "asset", "asset")
    _make_balance(client, from_id, "2026-04", 5000)
    _make_balance(client, to_id, "2026-04", 1000)

    response = client.post(
        "/balances/transfer",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": 500,
            "month": "2026-04",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["from_balance"]["amount"] == 4500  # asset: decreases
    assert body["to_balance"]["amount"] == 1500  # asset: increases


def test_transfer_asset_to_liability(client: TestClient) -> None:
    from_id, to_id = _setup_two_accounts(client, "asset", "liability")
    _make_balance(client, from_id, "2026-04", 5000)
    _make_balance(client, to_id, "2026-04", 2000)

    response = client.post(
        "/balances/transfer",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": 500,
            "month": "2026-04",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["from_balance"]["amount"] == 4500  # asset: decreases
    assert body["to_balance"]["amount"] == 1500  # liability: decreases (paydown)


def test_transfer_liability_to_asset(client: TestClient) -> None:
    from_id, to_id = _setup_two_accounts(client, "liability", "asset")
    _make_balance(client, from_id, "2026-04", 3000)
    _make_balance(client, to_id, "2026-04", 1000)

    response = client.post(
        "/balances/transfer",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": 500,
            "month": "2026-04",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["from_balance"]["amount"] == 3500  # liability: increases (borrowing)
    assert body["to_balance"]["amount"] == 1500  # asset: increases


def test_transfer_liability_to_liability(client: TestClient) -> None:
    from_id, to_id = _setup_two_accounts(client, "liability", "liability")
    _make_balance(client, from_id, "2026-04", 3000)
    _make_balance(client, to_id, "2026-04", 1000)

    response = client.post(
        "/balances/transfer",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": 200,
            "month": "2026-04",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["from_balance"]["amount"] == 3200  # liability: increases
    assert body["to_balance"]["amount"] == 800  # liability: decreases


def test_transfer_missing_from_balance(client: TestClient) -> None:
    from_id, to_id = _setup_two_accounts(client)
    _make_balance(client, to_id, "2026-04", 1000)  # only to_account has a balance

    response = client.post(
        "/balances/transfer",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": 100,
            "month": "2026-04",
        },
    )
    assert response.status_code == 422


def test_transfer_missing_to_balance(client: TestClient) -> None:
    from_id, to_id = _setup_two_accounts(client)
    _make_balance(client, from_id, "2026-04", 1000)  # only from_account has a balance

    response = client.post(
        "/balances/transfer",
        json={
            "from_account_id": from_id,
            "to_account_id": to_id,
            "amount": 100,
            "month": "2026-04",
        },
    )
    assert response.status_code == 422


def test_transfer_account_not_found(client: TestClient) -> None:
    from_id, _ = _setup_two_accounts(client)
    _make_balance(client, from_id, "2026-04", 1000)

    response = client.post(
        "/balances/transfer",
        json={
            "from_account_id": from_id,
            "to_account_id": 9999,
            "amount": 100,
            "month": "2026-04",
        },
    )
    assert response.status_code == 404
