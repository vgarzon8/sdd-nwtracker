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


def export_to_zip(session: Session) -> bytes:
    """Export all tables to a ZIP archive containing one CSV per table."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("currencies.csv", _currencies_csv(session))
        zf.writestr("tags.csv", _tags_csv(session))
        zf.writestr("institutions.csv", _institutions_csv(session))
        zf.writestr("accounts.csv", _accounts_csv(session))
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
    currencies = session.exec(select(Currency)).all()
    return _write_csv(
        ["code", "name"],
        [[c.code, c.name] for c in currencies],
    )


def _tags_csv(session: Session) -> str:
    tags = session.exec(select(Tag)).all()
    return _write_csv(["name"], [[t.name] for t in tags])


def _institutions_csv(session: Session) -> str:
    institutions = session.exec(select(Institution)).all()
    return _write_csv(["name"], [[i.name] for i in institutions])


def _accounts_csv(session: Session) -> str:
    accounts = session.exec(select(Account)).all()

    inst_by_id: dict[int, str] = {
        i.id: i.name
        for i in session.exec(select(Institution)).all()
        if i.id is not None
    }
    tags_by_id: dict[int, str] = {
        t.id: t.name
        for t in session.exec(select(Tag)).all()
        if t.id is not None
    }

    account_tags = session.exec(select(AccountTag)).all()
    tag_map: dict[int, list[str]] = {}
    for at in account_tags:
        if at.account_id is not None and at.tag_id is not None:
            tag_name = tags_by_id.get(at.tag_id, "")
            if tag_name:
                tag_map.setdefault(at.account_id, []).append(tag_name)

    rows: list[list[str]] = []
    for a in accounts:
        tag_names = sorted(tag_map.get(a.id or 0, []))
        rows.append(
            [
                a.name,
                inst_by_id.get(a.institution_id, ""),
                a.currency_code,
                a.side.value,
                a.status.value,
                ";".join(tag_names),
            ]
        )

    return _write_csv(
        ["name", "institution_name", "currency_code", "side", "status", "tags"],
        rows,
    )


def _balances_csv(session: Session) -> str:
    acct_by_id: dict[int, str] = {
        a.id: a.name
        for a in session.exec(select(Account)).all()
        if a.id is not None
    }
    balances = session.exec(select(Balance)).all()
    return _write_csv(
        ["account_name", "month", "amount"],
        [
            [acct_by_id.get(b.account_id, ""), b.month, str(b.amount)]
            for b in balances
        ],
    )


def _exchange_rates_csv(session: Session) -> str:
    rates = session.exec(select(ExchangeRate)).all()
    return _write_csv(
        ["currency_code", "month", "rate"],
        [[r.currency_code, r.month, f"{r.rate:.4f}"] for r in rates],
    )
