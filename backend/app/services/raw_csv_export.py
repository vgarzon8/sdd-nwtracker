import csv
import io
import zipfile

from sqlmodel import Session, select

from app.models import (
    Account,
    AccountTag,
    Balance,
    Currency,
    ExchangeRate,
    Institution,
    Tag,
)


def export_raw_to_zip(session: Session) -> bytes:
    """Export all tables to a ZIP archive with schema-aligned CSVs (IDs and FK IDs)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("currencies.csv", _currencies_csv(session))
        zf.writestr("tags.csv", _tags_csv(session))
        zf.writestr("institutions.csv", _institutions_csv(session))
        zf.writestr("accounts.csv", _accounts_csv(session))
        zf.writestr("account_tags.csv", _account_tags_csv(session))
        zf.writestr("balances.csv", _balances_csv(session))
        zf.writestr("exchange_rates.csv", _exchange_rates_csv(session))
    return buf.getvalue()


def _write_csv(headers: list[str], rows: list[list[str]]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(headers)
    writer.writerows(rows)
    return out.getvalue()


def _currencies_csv(session: Session) -> str:
    rows = session.exec(select(Currency)).all()
    return _write_csv(["code", "name"], [[r.code, r.name] for r in rows])


def _tags_csv(session: Session) -> str:
    rows = session.exec(select(Tag)).all()
    return _write_csv(["id", "name"], [[str(r.id), r.name] for r in rows])


def _institutions_csv(session: Session) -> str:
    rows = session.exec(select(Institution)).all()
    return _write_csv(["id", "name"], [[str(r.id), r.name] for r in rows])


def _accounts_csv(session: Session) -> str:
    rows = session.exec(select(Account)).all()
    return _write_csv(
        ["id", "name", "institution_id", "currency_code", "side", "status"],
        [
            [
                str(r.id),
                r.name,
                str(r.institution_id),
                r.currency_code,
                r.side.value,
                r.status.value,
            ]
            for r in rows
        ],
    )


def _account_tags_csv(session: Session) -> str:
    rows = session.exec(select(AccountTag)).all()
    return _write_csv(
        ["account_id", "tag_id"],
        [[str(r.account_id), str(r.tag_id)] for r in rows],
    )


def _balances_csv(session: Session) -> str:
    rows = session.exec(select(Balance)).all()
    return _write_csv(
        ["id", "account_id", "month", "amount"],
        [[str(r.id), str(r.account_id), r.month, str(r.amount)] for r in rows],
    )


def _exchange_rates_csv(session: Session) -> str:
    rows = session.exec(select(ExchangeRate)).all()
    return _write_csv(
        ["id", "currency_code", "month", "rate"],
        [[str(r.id), r.currency_code, r.month, f"{r.rate:.4f}"] for r in rows],
    )
