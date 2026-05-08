import io
import zipfile
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    Account,
    AccountSide,
    AccountStatus,
    AccountTag,
    Balance,
    Currency,
    ExchangeRate,
    Institution,
    Tag,
)

# ---------------------------------------------------------------------------
# Helpers: build in-memory ZIP files from dicts of {filename: csv_str}
# ---------------------------------------------------------------------------


def _make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


_EMPTY_CSVS: dict[str, str] = {
    "currencies.csv": "code,name\n",
    "tags.csv": "name\n",
    "institutions.csv": "name\n",
    "accounts.csv": "name,institution_name,currency_code,side,status,tags\n",
    "balances.csv": "account_name,month,amount\n",
    "exchange_rates.csv": "currency_code,month,rate\n",
}

_MINIMAL_CSVS: dict[str, str] = {
    "currencies.csv": "code,name\nUSD,US Dollar\nCNY,Chinese Yuan\n",
    "tags.csv": "name\nchecking\nsavings\n",
    "institutions.csv": "name\nChase\nICBC\n",
    "accounts.csv": (
        "name,institution_name,currency_code,side,status,tags\n"
        "Chase Checking,Chase,USD,asset,active,checking\n"
        "ICBC Savings,ICBC,CNY,asset,active,savings\n"
    ),
    "balances.csv": (
        "account_name,month,amount\n"
        "Chase Checking,2024-01,15000\n"
        "ICBC Savings,2024-01,50000\n"
    ),
    "exchange_rates.csv": "currency_code,month,rate\nCNY,2024-01,7.1000\n",
}


def _seed_minimal(session: Session) -> None:
    """Insert minimal fixture data matching _MINIMAL_CSVS."""
    session.add(Currency(code="USD", name="US Dollar"))
    session.add(Currency(code="CNY", name="Chinese Yuan"))
    session.flush()

    tag_chk = Tag(name="checking")
    tag_sav = Tag(name="savings")
    session.add(tag_chk)
    session.add(tag_sav)
    session.flush()

    inst_chase = Institution(name="Chase")
    inst_icbc = Institution(name="ICBC")
    session.add(inst_chase)
    session.add(inst_icbc)
    session.flush()

    acct_chase = Account(
        name="Chase Checking",
        institution_id=inst_chase.id,  # type: ignore[arg-type]
        currency_code="USD",
        side=AccountSide.asset,
        status=AccountStatus.active,
    )
    acct_icbc = Account(
        name="ICBC Savings",
        institution_id=inst_icbc.id,  # type: ignore[arg-type]
        currency_code="CNY",
        side=AccountSide.asset,
        status=AccountStatus.active,
    )
    session.add(acct_chase)
    session.add(acct_icbc)
    session.flush()

    session.add(AccountTag(account_id=acct_chase.id, tag_id=tag_chk.id))
    session.add(AccountTag(account_id=acct_icbc.id, tag_id=tag_sav.id))

    session.add(Balance(account_id=acct_chase.id, month="2024-01", amount=15000))  # type: ignore[arg-type]
    session.add(Balance(account_id=acct_icbc.id, month="2024-01", amount=50000))  # type: ignore[arg-type]

    session.add(
        ExchangeRate(currency_code="CNY", month="2024-01", rate=Decimal("7.1000"))
    )
    session.flush()


# ---------------------------------------------------------------------------
# Tests — export
# ---------------------------------------------------------------------------


def test_export_shape(client: TestClient, session: Session) -> None:
    """Export returns valid ZIP with all 6 CSVs and correct headers."""
    _seed_minimal(session)

    resp = client.get("/export")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = set(zf.namelist())
    assert names == {
        "currencies.csv",
        "tags.csv",
        "institutions.csv",
        "accounts.csv",
        "balances.csv",
        "exchange_rates.csv",
    }

    import csv

    def _headers(name: str) -> list[str]:
        rows = list(csv.DictReader(io.StringIO(zf.read(name).decode())))
        return (
            list(rows[0].keys())
            if rows
            else list(csv.reader(io.StringIO(zf.read(name).decode())))
            .__iter__()
            .__next__()
        )

    # Check headers via DictReader fieldnames
    def _fieldnames(name: str) -> list[str]:
        reader = csv.DictReader(io.StringIO(zf.read(name).decode()))
        return list(reader.fieldnames or [])

    assert _fieldnames("currencies.csv") == ["code", "name"]
    assert _fieldnames("tags.csv") == ["name"]
    assert _fieldnames("institutions.csv") == ["name"]
    assert _fieldnames("accounts.csv") == [
        "name",
        "institution_name",
        "currency_code",
        "side",
        "status",
        "tags",
    ]
    assert _fieldnames("balances.csv") == ["account_name", "month", "amount"]
    assert _fieldnames("exchange_rates.csv") == ["currency_code", "month", "rate"]


def test_export_uses_natural_keys(client: TestClient, session: Session) -> None:
    """Exported CSVs use human-readable names, not integer IDs."""
    _seed_minimal(session)

    resp = client.get("/export")
    zf = zipfile.ZipFile(io.BytesIO(resp.content))

    import csv

    accts = list(csv.DictReader(io.StringIO(zf.read("accounts.csv").decode())))
    chase = next(a for a in accts if a["name"] == "Chase Checking")
    assert chase["institution_name"] == "Chase"
    assert chase["currency_code"] == "USD"
    assert chase["tags"] == "checking"

    bals = list(csv.DictReader(io.StringIO(zf.read("balances.csv").decode())))
    b = next(b for b in bals if b["account_name"] == "Chase Checking")
    assert b["month"] == "2024-01"
    assert b["amount"] == "15000"


# ---------------------------------------------------------------------------
# Tests — import
# ---------------------------------------------------------------------------


def test_import_empty_csvs(client: TestClient) -> None:
    """Importing headers-only CSVs returns 200 with all counts zero."""
    resp = client.post(
        "/import",
        files={"file": ("export.zip", _make_zip(_EMPTY_CSVS), "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()["imported"]
    for table in (
        "currencies",
        "tags",
        "institutions",
        "accounts",
        "balances",
        "exchange_rates",
    ):
        assert data[table]["inserted"] == 0
        assert data[table]["updated"] == 0


def test_import_inserts_new_rows(client: TestClient, session: Session) -> None:
    """Importing minimal CSVs into an empty DB inserts all rows."""
    resp = client.post(
        "/import",
        files={"file": ("export.zip", _make_zip(_MINIMAL_CSVS), "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()["imported"]
    assert data["currencies"]["inserted"] == 2
    assert data["tags"]["inserted"] == 2
    assert data["institutions"]["inserted"] == 2
    assert data["accounts"]["inserted"] == 2
    assert data["balances"]["inserted"] == 2
    assert data["exchange_rates"]["inserted"] == 1

    # Verify DB state
    assert len(session.exec(select(Balance)).all()) == 2
    assert len(session.exec(select(AccountTag)).all()) == 2


def test_import_idempotent(client: TestClient) -> None:
    """Importing the same ZIP twice: second run has inserted=0."""
    zip_bytes = _make_zip(_MINIMAL_CSVS)
    client.post("/import", files={"file": ("e.zip", zip_bytes, "application/zip")})

    resp = client.post(
        "/import", files={"file": ("e.zip", zip_bytes, "application/zip")}
    )
    assert resp.status_code == 200
    data = resp.json()["imported"]
    assert data["currencies"]["inserted"] == 0
    assert data["tags"]["inserted"] == 0
    assert data["institutions"]["inserted"] == 0
    assert data["accounts"]["inserted"] == 0
    assert data["balances"]["inserted"] == 0
    assert data["exchange_rates"]["inserted"] == 0


def test_import_upserts_updated_amount(client: TestClient, session: Session) -> None:
    """Importing a ZIP with a different balance amount overwrites the existing row."""
    zip_bytes = _make_zip(_MINIMAL_CSVS)
    client.post("/import", files={"file": ("e.zip", zip_bytes, "application/zip")})

    updated_csvs = dict(_MINIMAL_CSVS)
    updated_csvs["balances.csv"] = (
        "account_name,month,amount\n"
        "Chase Checking,2024-01,99999\n"
        "ICBC Savings,2024-01,50000\n"
    )
    resp = client.post(
        "/import",
        files={"file": ("e.zip", _make_zip(updated_csvs), "application/zip")},
    )
    assert resp.status_code == 200
    assert resp.json()["imported"]["balances"]["updated"] == 2

    acct = session.exec(select(Account).where(Account.name == "Chase Checking")).first()
    assert acct is not None
    bal = session.exec(
        select(Balance).where(Balance.account_id == acct.id, Balance.month == "2024-01")
    ).first()
    assert bal is not None
    assert bal.amount == 99999


def test_import_tag_round_trip(client: TestClient, session: Session) -> None:
    """Tags embedded in accounts.csv are restored as AccountTag rows on import."""
    multi_tag_csvs = dict(_MINIMAL_CSVS)
    multi_tag_csvs["tags.csv"] = "name\nretirement\nbrokerage\n"
    multi_tag_csvs["accounts.csv"] = (
        "name,institution_name,currency_code,side,status,tags\n"
        "Chase Checking,Chase,USD,asset,active,retirement;brokerage\n"
        "ICBC Savings,ICBC,CNY,asset,active,\n"
    )

    resp = client.post(
        "/import",
        files={"file": ("e.zip", _make_zip(multi_tag_csvs), "application/zip")},
    )
    assert resp.status_code == 200

    acct = session.exec(select(Account).where(Account.name == "Chase Checking")).first()
    assert acct is not None
    at_rows = session.exec(
        select(AccountTag).where(
            AccountTag.account_id == acct.id  # type: ignore[arg-type]
        )
    ).all()
    assert len(at_rows) == 2

    untagged = session.exec(
        select(Account).where(Account.name == "ICBC Savings")
    ).first()
    assert untagged is not None
    at_none = session.exec(
        select(AccountTag).where(
            AccountTag.account_id == untagged.id  # type: ignore[arg-type]
        )
    ).all()
    assert len(at_none) == 0


def test_round_trip(client: TestClient, session: Session) -> None:
    """Export → delete data → import restores all rows."""
    _seed_minimal(session)
    session.flush()

    # Export
    resp = client.get("/export")
    assert resp.status_code == 200
    zip_bytes = resp.content

    # Wipe everything except currencies (to satisfy FK constraints in correct order)
    for at in session.exec(select(AccountTag)).all():
        session.delete(at)
    for b in session.exec(select(Balance)).all():
        session.delete(b)
    for er in session.exec(select(ExchangeRate)).all():
        session.delete(er)
    for a in session.exec(select(Account)).all():
        session.delete(a)
    for i in session.exec(select(Institution)).all():
        session.delete(i)
    for t in session.exec(select(Tag)).all():
        session.delete(t)
    session.flush()

    assert len(session.exec(select(Balance)).all()) == 0

    # Import
    resp2 = client.post(
        "/import",
        files={"file": ("export.zip", zip_bytes, "application/zip")},
    )
    assert resp2.status_code == 200
    data = resp2.json()["imported"]
    assert data["balances"]["inserted"] == 2
    assert data["accounts"]["inserted"] == 2
    assert data["exchange_rates"]["inserted"] == 1

    # Verify AccountTag rows restored
    assert len(session.exec(select(AccountTag)).all()) == 2


# ---------------------------------------------------------------------------
# Tests — import validation errors
# ---------------------------------------------------------------------------


def test_import_missing_file_422(client: TestClient) -> None:
    """ZIP missing balances.csv → 422 naming the file."""
    csvs = dict(_MINIMAL_CSVS)
    del csvs["balances.csv"]
    resp = client.post(
        "/import",
        files={"file": ("e.zip", _make_zip(csvs), "application/zip")},
    )
    assert resp.status_code == 422
    assert "balances.csv" in str(resp.json()["detail"]["missing"])


def test_import_invalid_month_422(client: TestClient) -> None:
    """balances.csv with invalid month format → 422."""
    csvs = dict(_MINIMAL_CSVS)
    csvs["balances.csv"] = (
        "account_name,month,amount\nChase Checking,January 2024,15000\n"
    )
    resp = client.post(
        "/import",
        files={"file": ("e.zip", _make_zip(csvs), "application/zip")},
    )
    assert resp.status_code == 422
    errors = resp.json()["detail"]["errors"]
    assert any("month" in e for e in errors)


def test_import_invalid_side_422(client: TestClient) -> None:
    """accounts.csv with invalid side value → 422."""
    csvs = dict(_MINIMAL_CSVS)
    csvs["accounts.csv"] = (
        "name,institution_name,currency_code,side,status,tags\n"
        "Chase Checking,Chase,USD,savings,active,\n"
        "ICBC Savings,ICBC,CNY,asset,active,\n"
    )
    resp = client.post(
        "/import",
        files={"file": ("e.zip", _make_zip(csvs), "application/zip")},
    )
    assert resp.status_code == 422
    errors = resp.json()["detail"]["errors"]
    assert any("side" in e for e in errors)


def test_import_unknown_institution_422(client: TestClient) -> None:
    """accounts.csv referencing unknown institution → 422."""
    csvs = dict(_MINIMAL_CSVS)
    csvs["accounts.csv"] = (
        "name,institution_name,currency_code,side,status,tags\n"
        "Chase Checking,NoSuchBank,USD,asset,active,\n"
        "ICBC Savings,ICBC,CNY,asset,active,\n"
    )
    resp = client.post(
        "/import",
        files={"file": ("e.zip", _make_zip(csvs), "application/zip")},
    )
    assert resp.status_code == 422
    errors = resp.json()["detail"]["errors"]
    assert any("institution_name" in e for e in errors)


def test_import_unknown_account_in_balances_422(client: TestClient) -> None:
    """balances.csv referencing unknown account_name → 422."""
    csvs = dict(_MINIMAL_CSVS)
    csvs["balances.csv"] = "account_name,month,amount\nNoSuchAccount,2024-01,15000\n"
    resp = client.post(
        "/import",
        files={"file": ("e.zip", _make_zip(csvs), "application/zip")},
    )
    assert resp.status_code == 422
    errors = resp.json()["detail"]["errors"]
    assert any("account_name" in e for e in errors)
