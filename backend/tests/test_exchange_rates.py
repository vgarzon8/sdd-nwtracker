from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_currency(client: TestClient, code: str = "USD") -> None:
    client.post("/currencies", json={"code": code, "name": f"{code} Currency"})


def _make_exchange_rate(
    client: TestClient,
    currency_code: str = "EUR",
    month: str = "2026-03",
    rate: str = "1.0800",
) -> dict:  # type: ignore[type-arg]
    return client.post(
        "/exchange-rates",
        json={"currency_code": currency_code, "month": month, "rate": rate},
    ).json()


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


def test_list_exchange_rates_empty(client: TestClient) -> None:
    assert client.get("/exchange-rates").status_code == 200
    assert client.get("/exchange-rates").json() == []


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_exchange_rate(client: TestClient) -> None:
    _make_currency(client, "EUR")
    response = client.post(
        "/exchange-rates",
        json={"currency_code": "EUR", "month": "2026-03", "rate": "7.1000"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["currency_code"] == "EUR"
    assert body["month"] == "2026-03"
    assert body["rate"] == "7.1000"
    assert isinstance(body["id"], int)


def test_create_exchange_rate_duplicate(client: TestClient) -> None:
    _make_currency(client, "EUR")
    client.post(
        "/exchange-rates",
        json={"currency_code": "EUR", "month": "2026-03", "rate": "1.08"},
    )
    response = client.post(
        "/exchange-rates",
        json={"currency_code": "EUR", "month": "2026-03", "rate": "1.09"},
    )
    assert response.status_code == 409


def test_create_exchange_rate_invalid_currency(client: TestClient) -> None:
    response = client.post(
        "/exchange-rates",
        json={"currency_code": "ZZZ", "month": "2026-03", "rate": "1.5"},
    )
    assert response.status_code == 404


def test_create_exchange_rate_zero_rate(client: TestClient) -> None:
    _make_currency(client, "EUR")
    response = client.post(
        "/exchange-rates",
        json={"currency_code": "EUR", "month": "2026-03", "rate": "0"},
    )
    assert response.status_code == 422


def test_create_exchange_rate_negative_rate(client: TestClient) -> None:
    _make_currency(client, "EUR")
    response = client.post(
        "/exchange-rates",
        json={"currency_code": "EUR", "month": "2026-03", "rate": "-1"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------


def test_get_exchange_rate(client: TestClient) -> None:
    _make_currency(client, "EUR")
    rate_id = _make_exchange_rate(client, "EUR", "2026-03", "1.0800")["id"]
    response = client.get(f"/exchange-rates/{rate_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == rate_id
    assert body["currency_code"] == "EUR"
    assert body["month"] == "2026-03"
    assert body["rate"] == "1.0800"


def test_get_exchange_rate_not_found(client: TestClient) -> None:
    assert client.get("/exchange-rates/9999").status_code == 404


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_exchange_rate(client: TestClient) -> None:
    _make_currency(client, "EUR")
    rate_id = _make_exchange_rate(client, "EUR", "2026-03", "1.0800")["id"]
    response = client.put(f"/exchange-rates/{rate_id}", json={"rate": "1.0900"})
    assert response.status_code == 200
    assert response.json()["rate"] == "1.0900"
    # Verify persisted
    assert client.get(f"/exchange-rates/{rate_id}").json()["rate"] == "1.0900"


def test_update_exchange_rate_not_found(client: TestClient) -> None:
    assert client.put("/exchange-rates/9999", json={"rate": "1.5"}).status_code == 404


def test_update_exchange_rate_zero_rate(client: TestClient) -> None:
    _make_currency(client, "EUR")
    rate_id = _make_exchange_rate(client)["id"]
    assert client.put(f"/exchange-rates/{rate_id}", json={"rate": "0"}).status_code == 422


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_exchange_rate(client: TestClient) -> None:
    _make_currency(client, "EUR")
    rate_id = _make_exchange_rate(client)["id"]
    assert client.delete(f"/exchange-rates/{rate_id}").status_code == 204
    assert client.get(f"/exchange-rates/{rate_id}").status_code == 404


def test_delete_exchange_rate_not_found(client: TestClient) -> None:
    assert client.delete("/exchange-rates/9999").status_code == 404


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------


def test_list_filter_by_currency(client: TestClient) -> None:
    _make_currency(client, "EUR")
    _make_currency(client, "CNY")
    _make_exchange_rate(client, "EUR", "2026-03", "1.08")
    _make_exchange_rate(client, "EUR", "2026-04", "1.09")
    _make_exchange_rate(client, "CNY", "2026-03", "7.10")

    results = client.get("/exchange-rates?currency=EUR").json()
    assert len(results) == 2
    assert all(r["currency_code"] == "EUR" for r in results)


def test_list_filter_by_month(client: TestClient) -> None:
    _make_currency(client, "EUR")
    _make_currency(client, "CNY")
    _make_exchange_rate(client, "EUR", "2026-03", "1.08")
    _make_exchange_rate(client, "EUR", "2026-04", "1.09")
    _make_exchange_rate(client, "CNY", "2026-03", "7.10")

    results = client.get("/exchange-rates?month=2026-03").json()
    assert len(results) == 2
    assert all(r["month"] == "2026-03" for r in results)


def test_list_filter_by_currency_and_month(client: TestClient) -> None:
    _make_currency(client, "EUR")
    _make_currency(client, "CNY")
    _make_exchange_rate(client, "EUR", "2026-03", "1.08")
    _make_exchange_rate(client, "EUR", "2026-04", "1.09")
    _make_exchange_rate(client, "CNY", "2026-03", "7.10")

    results = client.get("/exchange-rates?currency=EUR&month=2026-03").json()
    assert len(results) == 1
    assert results[0]["currency_code"] == "EUR"
    assert results[0]["month"] == "2026-03"


def test_list_filter_no_match(client: TestClient) -> None:
    _make_currency(client, "EUR")
    _make_exchange_rate(client, "EUR", "2026-03", "1.08")

    results = client.get("/exchange-rates?currency=EUR&month=2026-99").json()
    assert results == []


# ---------------------------------------------------------------------------
# Precision
# ---------------------------------------------------------------------------


def test_rate_precision_preserved(client: TestClient) -> None:
    _make_currency(client, "GBP")
    rate_id = client.post(
        "/exchange-rates",
        json={"currency_code": "GBP", "month": "2026-03", "rate": "0.9150"},
    ).json()["id"]
    body = client.get(f"/exchange-rates/{rate_id}").json()
    # Must come back as the 4dp string, not as a float like 0.915
    assert body["rate"] == "0.9150"
