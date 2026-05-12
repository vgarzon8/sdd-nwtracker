import csv
import io
import re
import zipfile
from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from pydantic import BaseModel
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

_EXPECTED_FILES = {
    "currencies.csv",
    "tags.csv",
    "institutions.csv",
    "accounts.csv",
    "balances.csv",
    "exchange_rates.csv",
}

_MONTH_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


class TableCounts(BaseModel):
    inserted: int
    updated: int


class ImportResult(BaseModel):
    imported: dict[str, TableCounts]
    skipped: dict[str, int] = {}
    warnings: list[str] = []


def import_from_zip(zip_bytes: bytes, session: Session) -> ImportResult:
    """Validate and upsert all rows from a ZIP archive into the DB.

    Raises HTTPException(422) if the ZIP is invalid, files are missing, or
    any row fails validation. All upserts run inside the caller's transaction;
    the caller is responsible for committing.
    """
    # --- Open ZIP ---
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=422, detail="Invalid ZIP file")

    present = set(zf.namelist())
    missing_files = sorted(_EXPECTED_FILES - present)
    if missing_files:
        raise HTTPException(
            status_code=422,
            detail={"message": "Missing files in ZIP", "missing": missing_files},
        )

    # --- Parse CSVs ---
    def _parse(name: str) -> list[dict[str, str]]:
        content = zf.read(name).decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))

    currencies_rows = _parse("currencies.csv")
    tags_rows = _parse("tags.csv")
    institutions_rows = _parse("institutions.csv")
    accounts_rows = _parse("accounts.csv")
    balances_rows = _parse("balances.csv")
    exchange_rates_rows = _parse("exchange_rates.csv")

    # --- Validate (collect all errors before touching the DB) ---
    errors: list[str] = []

    currency_codes = {r["code"] for r in currencies_rows if r.get("code")}
    inst_names = {r["name"] for r in institutions_rows if r.get("name")}
    account_names = {r["name"] for r in accounts_rows if r.get("name")}

    for i, r in enumerate(currencies_rows, 1):
        if not r.get("code"):
            errors.append(f"currencies.csv row {i}: 'code' is required")
        if not r.get("name"):
            errors.append(f"currencies.csv row {i}: 'name' is required")

    for i, r in enumerate(tags_rows, 1):
        if not r.get("name"):
            errors.append(f"tags.csv row {i}: 'name' is required")

    for i, r in enumerate(institutions_rows, 1):
        if not r.get("name"):
            errors.append(f"institutions.csv row {i}: 'name' is required")

    for i, r in enumerate(accounts_rows, 1):
        if r.get("institution_name", "") not in inst_names:
            errors.append(
                f"accounts.csv row {i}: unknown institution_name"
                f" '{r.get('institution_name')}'"
            )
        if r.get("currency_code", "") not in currency_codes:
            errors.append(
                f"accounts.csv row {i}: unknown currency_code"
                f" '{r.get('currency_code')}'"
            )
        if r.get("side") not in {"asset", "liability"}:
            errors.append(
                f"accounts.csv row {i}: 'side' must be 'asset' or 'liability',"
                f" got '{r.get('side')}'"
            )
        if r.get("status") not in {"active", "closed"}:
            errors.append(
                f"accounts.csv row {i}: 'status' must be 'active' or 'closed',"
                f" got '{r.get('status')}'"
            )

    for i, r in enumerate(balances_rows, 1):
        if r.get("account_name", "") not in account_names:
            errors.append(
                f"balances.csv row {i}: unknown account_name '{r.get('account_name')}'"
            )
        if not _MONTH_RE.match(r.get("month", "")):
            errors.append(
                f"balances.csv row {i}: invalid month '{r.get('month')}',"
                f" expected YYYY-MM"
            )
        try:
            int(r.get("amount", ""))
        except (ValueError, TypeError):
            errors.append(
                f"balances.csv row {i}: 'amount' must be an integer,"
                f" got '{r.get('amount')}'"
            )

    for i, r in enumerate(exchange_rates_rows, 1):
        if r.get("currency_code", "") not in currency_codes:
            errors.append(
                f"exchange_rates.csv row {i}: unknown currency_code"
                f" '{r.get('currency_code')}'"
            )
        if not _MONTH_RE.match(r.get("month", "")):
            errors.append(
                f"exchange_rates.csv row {i}: invalid month '{r.get('month')}',"
                f" expected YYYY-MM"
            )
        try:
            Decimal(r.get("rate", ""))
        except (InvalidOperation, TypeError):
            errors.append(
                f"exchange_rates.csv row {i}: 'rate' must be numeric,"
                f" got '{r.get('rate')}'"
            )

    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    # --- Upsert (all within the caller's transaction) ---
    counts: dict[str, TableCounts] = {}

    # 1. Currencies
    c_ins = c_upd = 0
    for r in currencies_rows:
        existing = session.exec(
            select(Currency).where(Currency.code == r["code"])
        ).first()
        if existing:
            existing.name = r["name"]
            session.add(existing)
            c_upd += 1
        else:
            session.add(Currency(code=r["code"], name=r["name"]))
            c_ins += 1
    session.flush()
    counts["currencies"] = TableCounts(inserted=c_ins, updated=c_upd)

    # 2. Tags
    t_ins = t_upd = 0
    for r in tags_rows:
        existing_tag: Tag | None = session.exec(
            select(Tag).where(Tag.name == r["name"])
        ).first()
        if existing_tag:
            t_upd += 1
        else:
            session.add(Tag(name=r["name"]))
            t_ins += 1
    session.flush()
    counts["tags"] = TableCounts(inserted=t_ins, updated=t_upd)

    # 3. Institutions
    i_ins = i_upd = 0
    for r in institutions_rows:
        existing_inst: Institution | None = session.exec(
            select(Institution).where(Institution.name == r["name"])
        ).first()
        if existing_inst:
            i_upd += 1
        else:
            session.add(Institution(name=r["name"]))
            i_ins += 1
    session.flush()
    counts["institutions"] = TableCounts(inserted=i_ins, updated=i_upd)

    # 4. Accounts (+ AccountTag)
    inst_id_map: dict[str, int] = {
        inst.name: inst.id
        for inst in session.exec(select(Institution)).all()
        if inst.id is not None
    }
    tag_id_map: dict[str, int] = {
        tag.name: tag.id
        for tag in session.exec(select(Tag)).all()
        if tag.id is not None
    }

    a_ins = a_upd = 0
    for r in accounts_rows:
        inst_id = inst_id_map[r["institution_name"]]
        tag_names_for_acct = [n for n in r.get("tags", "").split(";") if n]

        existing_acct: Account | None = session.exec(
            select(Account).where(Account.name == r["name"])
        ).first()
        if existing_acct:
            existing_acct.institution_id = inst_id
            existing_acct.currency_code = r["currency_code"]
            existing_acct.side = AccountSide(r["side"])
            existing_acct.status = AccountStatus(r["status"])
            session.add(existing_acct)
            acct_id = existing_acct.id
            a_upd += 1
        else:
            acct = Account(
                name=r["name"],
                institution_id=inst_id,
                currency_code=r["currency_code"],
                side=AccountSide(r["side"]),
                status=AccountStatus(r["status"]),
            )
            session.add(acct)
            session.flush()
            acct_id = acct.id
            a_ins += 1

        if acct_id is not None:
            # Replace AccountTag rows for this account
            old_tags = session.exec(
                select(AccountTag).where(
                    AccountTag.account_id == acct_id  # type: ignore[arg-type]
                )
            ).all()
            for at in old_tags:
                session.delete(at)
            session.flush()
            for tag_name in tag_names_for_acct:
                tag_id = tag_id_map.get(tag_name)
                if tag_id is not None:
                    session.add(AccountTag(account_id=acct_id, tag_id=tag_id))

    session.flush()
    counts["accounts"] = TableCounts(inserted=a_ins, updated=a_upd)

    # 5. Balances
    acct_id_map: dict[str, int] = {
        a.name: a.id for a in session.exec(select(Account)).all() if a.id is not None
    }

    b_ins = b_upd = 0
    for r in balances_rows:
        acct_id = acct_id_map[r["account_name"]]
        month = r["month"]
        amount = int(r["amount"])
        existing_bal: Balance | None = session.exec(
            select(Balance).where(
                Balance.account_id == acct_id,
                Balance.month == month,
            )
        ).first()
        if existing_bal:
            existing_bal.amount = amount
            session.add(existing_bal)
            b_upd += 1
        else:
            session.add(Balance(account_id=acct_id, month=month, amount=amount))
            b_ins += 1

    session.flush()
    counts["balances"] = TableCounts(inserted=b_ins, updated=b_upd)

    # 6. ExchangeRates
    er_ins = er_upd = 0
    for r in exchange_rates_rows:
        currency_code = r["currency_code"]
        month = r["month"]
        rate = Decimal(r["rate"])
        existing_er: ExchangeRate | None = session.exec(
            select(ExchangeRate).where(
                ExchangeRate.currency_code == currency_code,
                ExchangeRate.month == month,
            )
        ).first()
        if existing_er:
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

    return ImportResult(imported=counts)
