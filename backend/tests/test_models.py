from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
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


def _usd(session: Session) -> None:
    session.add(Currency(code="USD", name="US Dollar"))
    session.commit()


def _chase(session: Session) -> Institution:
    inst = Institution(name="Chase")
    session.add(inst)
    session.commit()
    return inst


def _checking(session: Session, inst: Institution) -> Account:
    assert inst.id is not None
    acct = Account(
        name="Checking",
        institution_id=inst.id,
        currency_code="USD",
        side=AccountSide.asset,
        status=AccountStatus.active,
    )
    session.add(acct)
    session.commit()
    return acct


# ---------------------------------------------------------------------------
# Currency
# ---------------------------------------------------------------------------


def test_currency_roundtrip(session: Session) -> None:
    session.add(Currency(code="USD", name="US Dollar"))
    session.commit()

    result = session.get(Currency, "USD")
    assert result is not None
    assert result.name == "US Dollar"


def test_currency_duplicate_pk_raises(session: Session) -> None:
    session.add(Currency(code="USD", name="US Dollar"))
    session.commit()
    session.add(Currency(code="USD", name="Duplicate"))
    with pytest.raises(IntegrityError):
        session.commit()


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------


def test_tag_roundtrip(session: Session) -> None:
    tag = Tag(name="savings")
    session.add(tag)
    session.commit()

    assert tag.id is not None
    result = session.get(Tag, tag.id)
    assert result is not None
    assert result.name == "savings"


def test_tag_unique_name_raises(session: Session) -> None:
    session.add(Tag(name="savings"))
    session.commit()
    session.add(Tag(name="savings"))
    with pytest.raises(IntegrityError):
        session.commit()


# ---------------------------------------------------------------------------
# Institution
# ---------------------------------------------------------------------------


def test_institution_roundtrip(session: Session) -> None:
    inst = Institution(name="Chase")
    session.add(inst)
    session.commit()

    assert inst.id is not None
    result = session.get(Institution, inst.id)
    assert result is not None
    assert result.name == "Chase"


def test_institution_unique_name_raises(session: Session) -> None:
    session.add(Institution(name="Chase"))
    session.commit()
    session.add(Institution(name="Chase"))
    with pytest.raises(IntegrityError):
        session.commit()


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


def test_account_roundtrip(session: Session) -> None:
    _usd(session)
    inst = _chase(session)
    assert inst.id is not None

    acct = Account(
        name="Chase Checking",
        institution_id=inst.id,
        currency_code="USD",
        side=AccountSide.asset,
        status=AccountStatus.active,
    )
    session.add(acct)
    session.commit()

    assert acct.id is not None
    result = session.get(Account, acct.id)
    assert result is not None
    assert result.side == AccountSide.asset
    assert result.status == AccountStatus.active
    assert result.currency_code == "USD"


def test_account_unique_name_raises(session: Session) -> None:
    _usd(session)
    inst = _chase(session)
    assert inst.id is not None

    session.add(
        Account(
            name="Checking",
            institution_id=inst.id,
            currency_code="USD",
            side=AccountSide.asset,
            status=AccountStatus.active,
        )
    )
    session.commit()
    session.add(
        Account(
            name="Checking",
            institution_id=inst.id,
            currency_code="USD",
            side=AccountSide.asset,
            status=AccountStatus.active,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_account_bad_institution_fk_raises(session: Session) -> None:
    _usd(session)
    session.add(
        Account(
            name="Orphan",
            institution_id=999,
            currency_code="USD",
            side=AccountSide.asset,
            status=AccountStatus.active,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_account_bad_currency_fk_raises(session: Session) -> None:
    inst = _chase(session)
    assert inst.id is not None
    session.add(
        Account(
            name="Orphan",
            institution_id=inst.id,
            currency_code="ZZZ",
            side=AccountSide.asset,
            status=AccountStatus.active,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


# ---------------------------------------------------------------------------
# AccountTag (join table)
# ---------------------------------------------------------------------------


def test_account_tag_roundtrip(session: Session) -> None:
    _usd(session)
    inst = _chase(session)
    acct = _checking(session, inst)
    tag = Tag(name="savings")
    session.add(tag)
    session.commit()

    assert acct.id is not None
    assert tag.id is not None
    session.add(AccountTag(account_id=acct.id, tag_id=tag.id))
    session.commit()

    result = session.exec(
        select(AccountTag).where(
            AccountTag.account_id == acct.id,
            AccountTag.tag_id == tag.id,
        )
    ).first()
    assert result is not None


# ---------------------------------------------------------------------------
# Balance
# ---------------------------------------------------------------------------


def test_balance_roundtrip(session: Session) -> None:
    _usd(session)
    inst = _chase(session)
    acct = _checking(session, inst)
    assert acct.id is not None

    bal = Balance(account_id=acct.id, month="2026-03", amount=15000)
    session.add(bal)
    session.commit()

    assert bal.id is not None
    result = session.get(Balance, bal.id)
    assert result is not None
    assert result.amount == 15000
    assert result.month == "2026-03"


def test_balance_composite_unique_raises(session: Session) -> None:
    _usd(session)
    inst = _chase(session)
    acct = _checking(session, inst)
    assert acct.id is not None

    session.add(Balance(account_id=acct.id, month="2026-03", amount=15000))
    session.commit()
    session.add(Balance(account_id=acct.id, month="2026-03", amount=20000))
    with pytest.raises(IntegrityError):
        session.commit()


# ---------------------------------------------------------------------------
# ExchangeRate
# ---------------------------------------------------------------------------


def test_exchange_rate_roundtrip(session: Session) -> None:
    session.add(Currency(code="CNY", name="Chinese Yuan"))
    session.commit()

    session.add(
        ExchangeRate(currency_code="CNY", month="2026-03", rate=Decimal("7.1000"))
    )
    session.commit()

    result = session.exec(select(ExchangeRate)).first()
    assert result is not None
    assert result.rate == Decimal("7.1")  # equality ignores trailing zeros
    assert result.currency_code == "CNY"


def test_exchange_rate_composite_unique_raises(session: Session) -> None:
    session.add(Currency(code="CNY", name="Chinese Yuan"))
    session.commit()

    session.add(
        ExchangeRate(currency_code="CNY", month="2026-03", rate=Decimal("7.1000"))
    )
    session.commit()
    session.add(
        ExchangeRate(currency_code="CNY", month="2026-03", rate=Decimal("7.2000"))
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_exchange_rate_bad_currency_fk_raises(session: Session) -> None:
    session.add(
        ExchangeRate(currency_code="ZZZ", month="2026-03", rate=Decimal("1.0000"))
    )
    with pytest.raises(IntegrityError):
        session.commit()
