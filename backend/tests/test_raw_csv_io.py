import csv
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
# Helpers
# ---------------------------------------------------------------------------


def _make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _fieldnames(zf: zipfile.ZipFile, name: str) -> list[str]:
    reader = csv.DictReader(io.StringIO(zf.read(name).decode()))
    return list(reader.fieldnames or [])


def _rows(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(zf.read(name).decode())))


_EMPTY_RAW_CSVS: dict[str, str] = {
    "currencies.csv": "code,name\n",
    "tags.csv": "id,name\n",
    "institutions.csv": "id,name\n",
    "accounts.csv": "id,name,institution_id,currency_code,side,status\n",
    "account_tags.csv": "account_id,tag_id\n",
    "balances.csv": "id,account_id,month,amount\n",
    "exchange_rates.csv": "id,currency_code,month,rate\n",
}


def _seed_and_export_raw(client: TestClient, session: Session) -> bytes:
    """Seed minimal data and return a raw ZIP export."""
    # Seed
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
    session.add(ExchangeRate(currency_code="CNY", month="2024-01", rate=Decimal("7.1000")))
    session.flush()

    resp = client.get("/export?format=raw")
    assert resp.status_code == 200
    return resp.content


# ---------------------------------------------------------------------------
# Tests — raw export
# ---------------------------------------------------------------------------


def test_raw_export_returns_7_csvs(client: TestClient, session: Session) -> None:
    """Raw export ZIP contains exactly the 7 schema-aligned CSVs."""
    _seed_and_export_raw(client, session)
    resp = client.get("/export?format=raw")
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    assert set(zf.namelist()) == {
        "currencies.csv",
        "tags.csv",
        "institutions.csv",
        "accounts.csv",
        "account_tags.csv",
        "balances.csv",
        "exchange_rates.csv",
    }


def test_raw_export_headers(client: TestClient, session: Session) -> None:
    """Raw export CSVs have schema-aligned headers (ids and FK id columns)."""
    zip_bytes = _seed_and_export_raw(client, session)
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))

    assert _fieldnames(zf, "currencies.csv") == ["code", "name"]
    assert _fieldnames(zf, "tags.csv") == ["id", "name"]
    assert _fieldnames(zf, "institutions.csv") == ["id", "name"]
    assert _fieldnames(zf, "accounts.csv") == [
        "id",
        "name",
        "institution_id",
        "currency_code",
        "side",
        "status",
    ]
    assert _fieldnames(zf, "account_tags.csv") == ["account_id", "tag_id"]
    assert _fieldnames(zf, "balances.csv") == ["id", "account_id", "month", "amount"]
    assert _fieldnames(zf, "exchange_rates.csv") == [
        "id",
        "currency_code",
        "month",
        "rate",
    ]


def test_raw_export_uses_integer_fks(client: TestClient, session: Session) -> None:
    """Raw export accounts.csv uses integer institution_id, not institution name."""
    zip_bytes = _seed_and_export_raw(client, session)
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))

    accts = _rows(zf, "accounts.csv")
    chase = next(a for a in accts if a["name"] == "Chase Checking")
    assert chase["institution_id"].isdigit()
    assert "institution_name" not in chase

    bals = _rows(zf, "balances.csv")
    bal = next(b for b in bals if b["amount"] == "15000")
    assert bal["account_id"].isdigit()
    assert "account_name" not in bal


def test_raw_export_filename(client: TestClient, session: Session) -> None:
    """Raw export uses nwtracker-raw-<date>.zip filename."""
    zip_bytes = _seed_and_export_raw(client, session)
    assert zip_bytes  # just exercise the endpoint; filename checked via header
    resp = client.get("/export?format=raw")
    cd = resp.headers.get("content-disposition", "")
    assert "nwtracker-raw-" in cd


def test_friendly_export_unchanged(client: TestClient, session: Session) -> None:
    """Default export (no format param) still returns the user-friendly format."""
    _seed_and_export_raw(client, session)
    resp = client.get("/export")
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    assert "account_tags.csv" not in zf.namelist()
    assert _fieldnames(zf, "accounts.csv") == [
        "name",
        "institution_name",
        "currency_code",
        "side",
        "status",
        "tags",
    ]


# ---------------------------------------------------------------------------
# Tests — raw import
# ---------------------------------------------------------------------------


def test_raw_import_empty_csvs(client: TestClient) -> None:
    """Importing headers-only raw CSVs returns 200 with all counts zero."""
    resp = client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", _make_zip(_EMPTY_RAW_CSVS), "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()["imported"]
    for table in (
        "currencies",
        "tags",
        "institutions",
        "accounts",
        "account_tags",
        "balances",
        "exchange_rates",
    ):
        assert data[table]["inserted"] == 0
        assert data[table]["updated"] == 0


def test_raw_import_inserts_rows(client: TestClient, session: Session) -> None:
    """Raw import inserts new rows across all tables."""
    zip_bytes = _seed_and_export_raw(client, session)

    # Clear everything
    _wipe_all(session)

    resp = client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", zip_bytes, "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()["imported"]
    assert data["currencies"]["inserted"] == 2
    assert data["tags"]["inserted"] == 2
    assert data["institutions"]["inserted"] == 2
    assert data["accounts"]["inserted"] == 2
    assert data["account_tags"]["inserted"] == 2
    assert data["balances"]["inserted"] == 2
    assert data["exchange_rates"]["inserted"] == 1


def test_raw_round_trip(client: TestClient, session: Session) -> None:
    """Raw export → wipe → raw import restores all data exactly."""
    zip_bytes = _seed_and_export_raw(client, session)

    # Capture reference state
    orig_bals = {
        b.amount for b in session.exec(select(Balance)).all()
    }
    orig_rates = {
        str(r.rate) for r in session.exec(select(ExchangeRate)).all()
    }

    _wipe_all(session)
    assert len(session.exec(select(Balance)).all()) == 0

    resp = client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", zip_bytes, "application/zip")},
    )
    assert resp.status_code == 200

    restored_bals = {b.amount for b in session.exec(select(Balance)).all()}
    restored_rates = {str(r.rate) for r in session.exec(select(ExchangeRate)).all()}
    assert restored_bals == orig_bals
    assert restored_rates == orig_rates
    assert len(session.exec(select(AccountTag)).all()) == 2


def test_raw_import_idempotent(client: TestClient, session: Session) -> None:
    """Importing the same raw ZIP twice: second run has inserted=0."""
    zip_bytes = _seed_and_export_raw(client, session)
    _wipe_all(session)

    client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", zip_bytes, "application/zip")},
    )
    resp = client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", zip_bytes, "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()["imported"]
    assert data["currencies"]["inserted"] == 0
    assert data["tags"]["inserted"] == 0
    assert data["institutions"]["inserted"] == 0
    assert data["accounts"]["inserted"] == 0
    assert data["balances"]["inserted"] == 0
    assert data["exchange_rates"]["inserted"] == 0


def test_raw_import_upserts_by_id(client: TestClient, session: Session) -> None:
    """Raw import updates an existing row when the id matches."""
    zip_bytes = _seed_and_export_raw(client, session)
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))

    # Modify balances.csv: change the first balance amount
    bals = _rows(zf, "balances.csv")
    bals[0]["amount"] = "99999"

    modified_files: dict[str, str] = {}
    for name in zf.namelist():
        if name == "balances.csv":
            out = io.StringIO()
            writer = csv.DictWriter(
                out,
                fieldnames=["id", "account_id", "month", "amount"],
            )
            writer.writeheader()
            writer.writerows(bals)
            modified_files[name] = out.getvalue()
        else:
            modified_files[name] = zf.read(name).decode()

    resp = client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", _make_zip(modified_files), "application/zip")},
    )
    assert resp.status_code == 200
    assert resp.json()["imported"]["balances"]["updated"] == 2

    amounts = {b.amount for b in session.exec(select(Balance)).all()}
    assert 99999 in amounts


def test_raw_import_skips_bad_fk_with_warning(client: TestClient) -> None:
    """A balance row with unknown account_id is skipped; warning is returned."""
    csvs = dict(_EMPTY_RAW_CSVS)
    csvs["currencies.csv"] = "code,name\nUSD,US Dollar\n"
    csvs["balances.csv"] = "id,account_id,month,amount\n,9999,2024-01,500\n"

    resp = client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", _make_zip(csvs), "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"].get("balances", 0) >= 1
    assert any("account_id" in w for w in data["warnings"])


def test_raw_import_skips_bad_institution_fk(client: TestClient) -> None:
    """An account row with unknown institution_id is skipped with a warning."""
    csvs = dict(_EMPTY_RAW_CSVS)
    csvs["currencies.csv"] = "code,name\nUSD,US Dollar\n"
    csvs["accounts.csv"] = (
        "id,name,institution_id,currency_code,side,status\n"
        ",My Account,9999,USD,asset,active\n"
    )

    resp = client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", _make_zip(csvs), "application/zip")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["skipped"].get("accounts", 0) >= 1
    assert any("institution_id" in w for w in data["warnings"])


def test_raw_import_missing_file_422(client: TestClient) -> None:
    """Raw ZIP missing account_tags.csv → 422."""
    csvs = dict(_EMPTY_RAW_CSVS)
    del csvs["account_tags.csv"]
    resp = client.post(
        "/import?format=raw",
        files={"file": ("raw.zip", _make_zip(csvs), "application/zip")},
    )
    assert resp.status_code == 422
    assert "account_tags.csv" in str(resp.json()["detail"]["missing"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _wipe_all(session: Session) -> None:
    for at in session.exec(select(AccountTag)).all():
        session.delete(at)
    for b in session.exec(select(Balance)).all():
        session.delete(b)
    for er in session.exec(select(ExchangeRate)).all():
        session.delete(er)
    for a in session.exec(select(Account)).all():
        session.delete(a)
    for inst in session.exec(select(Institution)).all():
        session.delete(inst)
    for t in session.exec(select(Tag)).all():
        session.delete(t)
    for c in session.exec(select(Currency)).all():
        session.delete(c)
    session.flush()
