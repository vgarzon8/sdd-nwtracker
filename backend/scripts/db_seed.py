from decimal import Decimal

from sqlmodel import Session

from app.db import engine, init_db
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


def seed() -> None:
    init_db()

    with Session(engine) as session:
        # --- Currencies ---
        for code, name in [
            ("USD", "US Dollar"),
            ("CNY", "Chinese Yuan"),
            ("CHF", "Swiss Franc"),
        ]:
            session.merge(Currency(code=code, name=name))

        # --- Tags ---  (id is stable so merge works)
        for tag_id, name in [
            (1, "retirement"),
            (2, "brokerage"),
            (3, "checking"),
            (4, "savings"),
        ]:
            session.merge(Tag(id=tag_id, name=name))

        # --- Institutions ---
        for inst_id, name in [
            (1, "Chase"),
            (2, "Fidelity"),
            (3, "ICBC"),
            (4, "UBS"),
        ]:
            session.merge(Institution(id=inst_id, name=name))

        session.flush()

        # --- Accounts ---
        _A, _L = AccountSide.asset, AccountSide.liability
        _open = AccountStatus.active
        for acct_id, name, inst_id, currency_code, side, status in [
            (1, "Chase Checking", 1, "USD", _A, _open),
            (2, "Chase Savings", 1, "USD", _A, _open),
            (3, "Fidelity 401k", 2, "USD", _A, _open),
            (4, "ICBC Savings", 3, "CNY", _A, _open),
            (5, "Chase Credit Card", 1, "USD", _L, _open),
        ]:
            session.merge(
                Account(
                    id=acct_id,
                    name=name,
                    institution_id=inst_id,
                    currency_code=currency_code,
                    side=side,
                    status=status,
                )
            )

        session.flush()

        # --- Account–Tag links ---
        for acct_id, tag_id in [
            (1, 3),  # Chase Checking → checking
            (2, 4),  # Chase Savings → savings
            (3, 1),  # Fidelity 401k → retirement
            (3, 2),  # Fidelity 401k → brokerage
            (4, 4),  # ICBC Savings → savings
        ]:
            session.merge(AccountTag(account_id=acct_id, tag_id=tag_id))

        # --- Balances (2026-03 and 2026-04) ---
        for bal_id, acct_id, month, amount in [
            (1, 1, "2026-03", 15000),
            (2, 1, "2026-04", 15500),
            (3, 2, "2026-03", 25000),
            (4, 2, "2026-04", 26000),
            (5, 3, "2026-03", 120000),
            (6, 3, "2026-04", 122000),
            (7, 4, "2026-03", 200000),
            (8, 4, "2026-04", 205000),
            (9, 5, "2026-03", 3500),
            (10, 5, "2026-04", 2800),
        ]:
            session.merge(
                Balance(id=bal_id, account_id=acct_id, month=month, amount=amount)
            )

        # --- Exchange rates ---
        for rate_id, currency_code, month, rate in [
            (1, "CNY", "2026-03", Decimal("7.1000")),
            (2, "CNY", "2026-04", Decimal("7.2000")),
            (3, "CHF", "2026-03", Decimal("0.8900")),
            (4, "CHF", "2026-04", Decimal("0.8850")),
        ]:
            session.merge(
                ExchangeRate(
                    id=rate_id,
                    currency_code=currency_code,
                    month=month,
                    rate=rate,
                )
            )

        session.commit()
        print("Seed data loaded.")


def main() -> None:
    seed()


if __name__ == "__main__":
    main()
