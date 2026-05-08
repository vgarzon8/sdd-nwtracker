from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_currency(client: TestClient, code: str = "USD") -> None:
    client.post("/currencies", json={"code": code, "name": f"{code} Currency"})


def _make_institution(client: TestClient, name: str = "Bank A") -> int:
    return client.post("/institutions", json={"name": name}).json()["id"]


def _make_tag(client: TestClient, name: str) -> int:
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


def _make_balance(client: TestClient, account_id: int, month: str, amount: int) -> None:
    client.post(
        "/balances", json={"account_id": account_id, "month": month, "amount": amount}
    )


def _make_exchange_rate(
    client: TestClient, currency_code: str, month: str, rate: str
) -> None:
    client.post(
        "/exchange-rates",
        json={"currency_code": currency_code, "month": month, "rate": rate},
    )


def _setup_base(client: TestClient) -> tuple[int, int]:
    """Create USD currency + institution. Return (inst_id, usd_currency_created)."""
    _make_currency(client, "USD")
    inst_id = _make_institution(client)
    return inst_id, 0


# ---------------------------------------------------------------------------
# Single-month endpoint — GET /reports/balance-summary
# ---------------------------------------------------------------------------


def test_side_usd_only(client: TestClient) -> None:
    inst_id = _make_institution(client)
    _make_currency(client, "USD")
    asset_id = _make_account(
        client, name="Savings", institution_id=inst_id, side="asset"
    )["id"]
    liability_id = _make_account(
        client, name="Mortgage", institution_id=inst_id, side="liability"
    )["id"]
    _make_balance(client, asset_id, "2024-01", 100_000)
    _make_balance(client, liability_id, "2024-01", 40_000)

    resp = client.get("/reports/balance-summary?attribute=side&month=2024-01")
    assert resp.status_code == 200
    items = {i["group_key"]: i["balance_sum_usd"] for i in resp.json()}
    assert items["asset"] == 100_000
    assert items["liability"] == 40_000


def test_side_multi_currency(client: TestClient) -> None:
    _make_currency(client, "USD")
    _make_currency(client, "CNY")
    inst_id = _make_institution(client)
    usd_id = _make_account(
        client, name="USD Savings", institution_id=inst_id, currency_code="USD"
    )["id"]
    cny_id = _make_account(
        client,
        name="CNY Savings",
        institution_id=inst_id,
        currency_code="CNY",
        side="asset",
    )["id"]
    _make_balance(client, usd_id, "2024-01", 10_000)
    _make_balance(client, cny_id, "2024-01", 71_000)
    _make_exchange_rate(client, "CNY", "2024-01", "7.1000")

    resp = client.get("/reports/balance-summary?attribute=side&month=2024-01")
    assert resp.status_code == 200
    items = {i["group_key"]: i["balance_sum_usd"] for i in resp.json()}
    # 71000 CNY / 7.1 = 10000 USD; total asset = 20000
    assert items["asset"] == 20_000


def test_attribute_currency(client: TestClient) -> None:
    _make_currency(client, "USD")
    _make_currency(client, "EUR")
    inst_id = _make_institution(client)
    usd_id = _make_account(
        client, name="USD Acc", institution_id=inst_id, currency_code="USD"
    )["id"]
    eur_id = _make_account(
        client, name="EUR Acc", institution_id=inst_id, currency_code="EUR"
    )["id"]
    _make_balance(client, usd_id, "2024-01", 5_000)
    _make_balance(client, eur_id, "2024-01", 10_800)
    _make_exchange_rate(client, "EUR", "2024-01", "0.9259")

    resp = client.get("/reports/balance-summary?attribute=currency&month=2024-01")
    assert resp.status_code == 200
    items = {i["group_key"]: i["balance_sum_usd"] for i in resp.json()}
    assert items["USD"] == 5_000
    assert items["EUR"] == round(10_800 / 0.9259)


def test_attribute_institution(client: TestClient) -> None:
    _make_currency(client, "USD")
    inst_a = _make_institution(client, "Bank A")
    inst_b = _make_institution(client, "Bank B")
    a1 = _make_account(
        client, name="A Checking", institution_id=inst_a, currency_code="USD"
    )["id"]
    a2 = _make_account(
        client, name="B Savings", institution_id=inst_b, currency_code="USD"
    )["id"]
    _make_balance(client, a1, "2024-01", 3_000)
    _make_balance(client, a2, "2024-01", 7_000)

    resp = client.get("/reports/balance-summary?attribute=institution&month=2024-01")
    assert resp.status_code == 200
    items = {i["group_key"]: i["balance_sum_usd"] for i in resp.json()}
    assert items[inst_a] == 3_000
    assert items[inst_b] == 7_000


def test_attribute_tags_multi_tag_account(client: TestClient) -> None:
    _make_currency(client, "USD")
    inst_id = _make_institution(client)
    tag_r = _make_tag(client, "retirement")
    tag_l = _make_tag(client, "liquid")
    acc_id = _make_account(
        client,
        name="401k",
        institution_id=inst_id,
        tag_ids=[tag_r, tag_l],
    )["id"]
    _make_balance(client, acc_id, "2024-01", 50_000)

    resp = client.get("/reports/balance-summary?attribute=tags&month=2024-01")
    assert resp.status_code == 200
    items = {i["group_key"]: i["balance_sum_usd"] for i in resp.json()}
    # Account appears in both tags
    assert items[tag_r] == 50_000
    assert items[tag_l] == 50_000
    assert None not in items


def test_attribute_tags_untagged_account(client: TestClient) -> None:
    _make_currency(client, "USD")
    inst_id = _make_institution(client)
    acc_id = _make_account(client, name="Untagged", institution_id=inst_id)["id"]
    _make_balance(client, acc_id, "2024-01", 1_000)

    resp = client.get("/reports/balance-summary?attribute=tags&month=2024-01")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["group_key"] is None
    assert items[0]["balance_sum_usd"] == 1_000


def test_missing_exchange_rate_returns_422(client: TestClient) -> None:
    _make_currency(client, "USD")
    _make_currency(client, "JPY")
    inst_id = _make_institution(client)
    acc_id = _make_account(
        client, name="JPY Acc", institution_id=inst_id, currency_code="JPY"
    )["id"]
    _make_balance(client, acc_id, "2024-01", 1_000_000)

    resp = client.get("/reports/balance-summary?attribute=side&month=2024-01")
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["missing"][0]["currency_code"] == "JPY"
    assert detail["missing"][0]["month"] == "2024-01"


def test_closed_account_omitted(client: TestClient) -> None:
    _make_currency(client, "USD")
    inst_id = _make_institution(client)
    acc_id = _make_account(
        client, name="Closed", institution_id=inst_id, status="closed"
    )["id"]
    _make_balance(client, acc_id, "2024-01", 999)

    resp = client.get("/reports/balance-summary?attribute=side&month=2024-01")
    assert resp.status_code == 200
    assert resp.json() == []


def test_active_account_no_balance_omitted(client: TestClient) -> None:
    _make_currency(client, "USD")
    inst_id = _make_institution(client)
    _make_account(client, name="No Balance", institution_id=inst_id)

    resp = client.get("/reports/balance-summary?attribute=side&month=2024-01")
    assert resp.status_code == 200
    assert resp.json() == []


def test_invalid_attribute_returns_422(client: TestClient) -> None:
    resp = client.get("/reports/balance-summary?attribute=banana&month=2024-01")
    assert resp.status_code == 422


def test_invalid_month_format_returns_422(client: TestClient) -> None:
    resp = client.get("/reports/balance-summary?attribute=side&month=2024-1")
    assert resp.status_code == 422


def test_month_with_no_data_returns_empty(client: TestClient) -> None:
    resp = client.get("/reports/balance-summary?attribute=side&month=2024-01")
    assert resp.status_code == 200
    assert resp.json() == []


# ---------------------------------------------------------------------------
# History endpoint — GET /reports/balance-summary/history
# ---------------------------------------------------------------------------


def test_history_happy_path(client: TestClient) -> None:
    _make_currency(client, "USD")
    inst_id = _make_institution(client)
    asset_id = _make_account(client, name="Savings", institution_id=inst_id)["id"]
    liab_id = _make_account(
        client, name="Loan", institution_id=inst_id, side="liability"
    )["id"]

    for month, amount in [
        ("2024-01", 100_000),
        ("2024-02", 105_000),
        ("2024-03", 110_000),
    ]:
        _make_balance(client, asset_id, month, amount)
        _make_balance(client, liab_id, month, 20_000)

    resp = client.get(
        "/reports/balance-summary/history?attribute=side&from=2024-01&to=2024-03"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["from_month"] == "2024-01"
    assert body["to_month"] == "2024-03"
    months = sorted({i["month"] for i in body["items"]})
    assert months == ["2024-01", "2024-02", "2024-03"]
    # Items are sorted by (month, group_key)
    assert body["items"][0]["month"] <= body["items"][-1]["month"]


def test_history_to_defaults_to_max_month(client: TestClient) -> None:
    _make_currency(client, "USD")
    inst_id = _make_institution(client)
    acc_id = _make_account(client, name="Savings", institution_id=inst_id)["id"]
    _make_balance(client, acc_id, "2024-01", 1_000)
    _make_balance(client, acc_id, "2024-06", 2_000)

    resp = client.get("/reports/balance-summary/history?attribute=side&from=2024-01")
    assert resp.status_code == 200
    assert resp.json()["to_month"] == "2024-06"


def test_history_months_with_no_data_omitted(client: TestClient) -> None:
    _make_currency(client, "USD")
    inst_id = _make_institution(client)
    acc_id = _make_account(client, name="Savings", institution_id=inst_id)["id"]
    _make_balance(client, acc_id, "2024-01", 1_000)
    _make_balance(client, acc_id, "2024-03", 3_000)
    # No balance for 2024-02

    resp = client.get(
        "/reports/balance-summary/history?attribute=side&from=2024-01&to=2024-03"
    )
    assert resp.status_code == 200
    months = {i["month"] for i in resp.json()["items"]}
    assert "2024-02" not in months
    assert months == {"2024-01", "2024-03"}


def test_history_missing_exchange_rate_returns_422(client: TestClient) -> None:
    _make_currency(client, "USD")
    _make_currency(client, "EUR")
    inst_id = _make_institution(client)
    acc_id = _make_account(
        client, name="EUR Acc", institution_id=inst_id, currency_code="EUR"
    )["id"]
    _make_balance(client, acc_id, "2024-01", 5_000)
    _make_balance(client, acc_id, "2024-02", 5_500)
    # Rate for 2024-01 provided; 2024-02 missing
    _make_exchange_rate(client, "EUR", "2024-01", "0.9200")

    resp = client.get(
        "/reports/balance-summary/history?attribute=side&from=2024-01&to=2024-02"
    )
    assert resp.status_code == 422
    missing = resp.json()["detail"]["missing"]
    assert any(m["currency_code"] == "EUR" and m["month"] == "2024-02" for m in missing)


def test_history_from_after_to_returns_422(client: TestClient) -> None:
    resp = client.get(
        "/reports/balance-summary/history?attribute=side&from=2024-06&to=2024-01"
    )
    assert resp.status_code == 422


def test_history_invalid_from_format_returns_422(client: TestClient) -> None:
    resp = client.get(
        "/reports/balance-summary/history?attribute=side&from=2024-1&to=2024-03"
    )
    assert resp.status_code == 422


def test_history_no_data_to_omitted_returns_empty(client: TestClient) -> None:
    resp = client.get("/reports/balance-summary/history?attribute=side&from=2024-01")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
