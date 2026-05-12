import csv
import io
import re
import zipfile
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
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
from app.services.csv_import import ImportResult, TableCounts

_EXPECTED_FILES = {
    "currencies.csv",
    "tags.csv",
    "institutions.csv",
    "accounts.csv",
    "account_tags.csv",
    "balances.csv",
    "exchange_rates.csv",
}

_MONTH_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


def import_raw_from_zip(zip_bytes: bytes, session: Session) -> ImportResult:
    """Upsert all rows from a schema-aligned ZIP archive.

    Rows with referential integrity violations are skipped with a warning.
    Import order: currencies → tags → institutions → accounts → account_tags
                  → balances → exchange_rates.
    The caller is responsible for committing the transaction.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=422, detail="Invalid ZIP file")

    present = set(zf.namelist())
    missing = sorted(_EXPECTED_FILES - present)
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"message": "Missing files in ZIP", "missing": missing},
        )

    def _parse(name: str) -> list[dict[str, str]]:
        content = zf.read(name).decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))

    currencies_rows = _parse("currencies.csv")
    tags_rows = _parse("tags.csv")
    institutions_rows = _parse("institutions.csv")
    accounts_rows = _parse("accounts.csv")
    account_tags_rows = _parse("account_tags.csv")
    balances_rows = _parse("balances.csv")
    exchange_rates_rows = _parse("exchange_rates.csv")

    counts: dict[str, TableCounts] = {}
    skipped: dict[str, int] = {}
    warnings: list[str] = []

    # 1. Currencies (PK = code, no surrogate id)
    c_ins = c_upd = 0
    for i, r in enumerate(currencies_rows, 1):
        code = r.get("code", "").strip()
        name = r.get("name", "").strip()
        if not code or not name:
            warnings.append(
                f"currencies.csv row {i}: missing 'code' or 'name' — skipped"
            )
            skipped["currencies"] = skipped.get("currencies", 0) + 1
            continue
        existing_cur = session.exec(
            select(Currency).where(Currency.code == code)
        ).first()
        if existing_cur:
            existing_cur.name = name
            session.add(existing_cur)
            c_upd += 1
        else:
            session.add(Currency(code=code, name=name))
            c_ins += 1
    session.flush()
    counts["currencies"] = TableCounts(inserted=c_ins, updated=c_upd)

    # Build lookup maps keyed by id (from DB after flush)
    currency_codes = {c.code for c in session.exec(select(Currency)).all()}

    # 2. Tags
    t_ins = t_upd = 0
    for i, r in enumerate(tags_rows, 1):
        raw_id = r.get("id", "").strip()
        name = r.get("name", "").strip()
        if not name:
            warnings.append(f"tags.csv row {i}: missing 'name' — skipped")
            skipped["tags"] = skipped.get("tags", 0) + 1
            continue
        row_id = _parse_int(raw_id)
        existing_tag: Tag | None = None
        if row_id is not None:
            existing_tag = session.exec(select(Tag).where(Tag.id == row_id)).first()
        if existing_tag:
            existing_tag.name = name
            session.add(existing_tag)
            t_upd += 1
        else:
            session.add(Tag(name=name))
            t_ins += 1
    session.flush()
    counts["tags"] = TableCounts(inserted=t_ins, updated=t_upd)

    tag_id_set = {t.id for t in session.exec(select(Tag)).all() if t.id is not None}

    # 3. Institutions
    i_ins = i_upd = 0
    for i, r in enumerate(institutions_rows, 1):
        raw_id = r.get("id", "").strip()
        name = r.get("name", "").strip()
        if not name:
            warnings.append(f"institutions.csv row {i}: missing 'name' — skipped")
            skipped["institutions"] = skipped.get("institutions", 0) + 1
            continue
        row_id = _parse_int(raw_id)
        existing_inst: Institution | None = None
        if row_id is not None:
            existing_inst = session.exec(
                select(Institution).where(Institution.id == row_id)
            ).first()
        if existing_inst:
            existing_inst.name = name
            session.add(existing_inst)
            i_upd += 1
        else:
            session.add(Institution(name=name))
            i_ins += 1
    session.flush()
    counts["institutions"] = TableCounts(inserted=i_ins, updated=i_upd)

    inst_id_set = {
        inst.id
        for inst in session.exec(select(Institution)).all()
        if inst.id is not None
    }

    # 4. Accounts
    a_ins = a_upd = 0
    for i, r in enumerate(accounts_rows, 1):
        raw_id = r.get("id", "").strip()
        name = r.get("name", "").strip()
        raw_inst_id = r.get("institution_id", "").strip()
        currency_code = r.get("currency_code", "").strip()
        side_val = r.get("side", "").strip()
        status_val = r.get("status", "").strip()

        inst_id = _parse_int(raw_inst_id)
        if inst_id not in inst_id_set:
            warnings.append(
                f"accounts.csv row {i}: unknown institution_id={raw_inst_id!r}"
                " — skipped"
            )
            skipped["accounts"] = skipped.get("accounts", 0) + 1
            continue
        if currency_code not in currency_codes:
            warnings.append(
                f"accounts.csv row {i}: unknown currency_code={currency_code!r}"
                " — skipped"
            )
            skipped["accounts"] = skipped.get("accounts", 0) + 1
            continue
        if side_val not in {"asset", "liability"}:
            warnings.append(
                f"accounts.csv row {i}: invalid side={side_val!r} — skipped"
            )
            skipped["accounts"] = skipped.get("accounts", 0) + 1
            continue
        if status_val not in {"active", "closed"}:
            warnings.append(
                f"accounts.csv row {i}: invalid status={status_val!r} — skipped"
            )
            skipped["accounts"] = skipped.get("accounts", 0) + 1
            continue
        if not name:
            warnings.append(f"accounts.csv row {i}: missing 'name' — skipped")
            skipped["accounts"] = skipped.get("accounts", 0) + 1
            continue

        row_id = _parse_int(raw_id)
        existing_acct: Account | None = None
        if row_id is not None:
            existing_acct = session.exec(
                select(Account).where(Account.id == row_id)
            ).first()
        if existing_acct:
            existing_acct.name = name
            existing_acct.institution_id = inst_id  # type: ignore[assignment]
            existing_acct.currency_code = currency_code
            existing_acct.side = AccountSide(side_val)
            existing_acct.status = AccountStatus(status_val)
            session.add(existing_acct)
            a_upd += 1
        else:
            session.add(
                Account(
                    name=name,
                    institution_id=inst_id,  # type: ignore[arg-type]
                    currency_code=currency_code,
                    side=AccountSide(side_val),
                    status=AccountStatus(status_val),
                )
            )
            a_ins += 1
    session.flush()
    counts["accounts"] = TableCounts(inserted=a_ins, updated=a_upd)

    account_id_set = {
        a.id for a in session.exec(select(Account)).all() if a.id is not None
    }

    # 5. AccountTags
    at_ins = at_upd = 0
    for i, r in enumerate(account_tags_rows, 1):
        raw_acct_id = r.get("account_id", "").strip()
        raw_tag_id = r.get("tag_id", "").strip()
        acct_id = _parse_int(raw_acct_id)
        tag_id = _parse_int(raw_tag_id)

        if acct_id not in account_id_set:
            warnings.append(
                f"account_tags.csv row {i}: unknown account_id={raw_acct_id!r}"
                " — skipped"
            )
            skipped["account_tags"] = skipped.get("account_tags", 0) + 1
            continue
        if tag_id not in tag_id_set:
            warnings.append(
                f"account_tags.csv row {i}: unknown tag_id={raw_tag_id!r} — skipped"
            )
            skipped["account_tags"] = skipped.get("account_tags", 0) + 1
            continue

        existing_at = session.exec(
            select(AccountTag).where(
                AccountTag.account_id == acct_id,  # type: ignore[arg-type]
                AccountTag.tag_id == tag_id,  # type: ignore[arg-type]
            )
        ).first()
        if existing_at:
            at_upd += 1
        else:
            session.add(AccountTag(account_id=acct_id, tag_id=tag_id))  # type: ignore[arg-type]
            at_ins += 1
    session.flush()
    counts["account_tags"] = TableCounts(inserted=at_ins, updated=at_upd)

    # 6. Balances
    b_ins = b_upd = 0
    for i, r in enumerate(balances_rows, 1):
        raw_id = r.get("id", "").strip()
        raw_acct_id = r.get("account_id", "").strip()
        month = r.get("month", "").strip()
        raw_amount = r.get("amount", "").strip()

        acct_id = _parse_int(raw_acct_id)
        if acct_id not in account_id_set:
            warnings.append(
                f"balances.csv row {i}: unknown account_id={raw_acct_id!r} — skipped"
            )
            skipped["balances"] = skipped.get("balances", 0) + 1
            continue
        if not _MONTH_RE.match(month):
            warnings.append(f"balances.csv row {i}: invalid month={month!r} — skipped")
            skipped["balances"] = skipped.get("balances", 0) + 1
            continue
        amount = _parse_int(raw_amount)
        if amount is None:
            warnings.append(
                f"balances.csv row {i}: non-integer amount={raw_amount!r} — skipped"
            )
            skipped["balances"] = skipped.get("balances", 0) + 1
            continue

        row_id = _parse_int(raw_id)
        existing_bal: Balance | None = None
        if row_id is not None:
            existing_bal = session.exec(
                select(Balance).where(Balance.id == row_id)
            ).first()
        if existing_bal:
            existing_bal.account_id = acct_id  # type: ignore[assignment]
            existing_bal.month = month
            existing_bal.amount = amount
            session.add(existing_bal)
            b_upd += 1
        else:
            session.add(Balance(account_id=acct_id, month=month, amount=amount))  # type: ignore[arg-type]
            b_ins += 1
    session.flush()
    counts["balances"] = TableCounts(inserted=b_ins, updated=b_upd)

    # 7. ExchangeRates
    er_ins = er_upd = 0
    for i, r in enumerate(exchange_rates_rows, 1):
        raw_id = r.get("id", "").strip()
        currency_code = r.get("currency_code", "").strip()
        month = r.get("month", "").strip()
        raw_rate = r.get("rate", "").strip()

        if currency_code not in currency_codes:
            warnings.append(
                f"exchange_rates.csv row {i}: unknown currency_code={currency_code!r}"
                " — skipped"
            )
            skipped["exchange_rates"] = skipped.get("exchange_rates", 0) + 1
            continue
        if not _MONTH_RE.match(month):
            warnings.append(
                f"exchange_rates.csv row {i}: invalid month={month!r} — skipped"
            )
            skipped["exchange_rates"] = skipped.get("exchange_rates", 0) + 1
            continue
        try:
            rate = Decimal(raw_rate)
        except (InvalidOperation, ValueError):
            warnings.append(
                f"exchange_rates.csv row {i}: non-numeric rate={raw_rate!r} — skipped"
            )
            skipped["exchange_rates"] = skipped.get("exchange_rates", 0) + 1
            continue

        row_id = _parse_int(raw_id)
        existing_er: ExchangeRate | None = None
        if row_id is not None:
            existing_er = session.exec(
                select(ExchangeRate).where(ExchangeRate.id == row_id)
            ).first()
        if existing_er:
            existing_er.currency_code = currency_code
            existing_er.month = month
            existing_er.rate = rate
            session.add(existing_er)
            er_upd += 1
        else:
            session.add(
                ExchangeRate(currency_code=currency_code, month=month, rate=rate)
            )
            er_ins += 1
    session.flush()
    counts["exchange_rates"] = TableCounts(inserted=er_ins, updated=er_upd)

    return ImportResult(imported=counts, skipped=skipped, warnings=warnings)


def _parse_int(value: str) -> int | None:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
