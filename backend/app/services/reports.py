import re
from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Account, AccountStatus, AccountTag, Balance, ExchangeRate
from app.models.report import (
    AccountAttribute,
    BalanceSummaryHistoryItem,
    BalanceSummaryHistoryResponse,
    BalanceSummaryItem,
)

_MONTH_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")


def _validate_month(month: str) -> None:
    if not _MONTH_RE.match(month):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid month format '{month}'. Expected YYYY-MM.",
        )


def _compute_groups(
    rows: list[tuple[Account, int]],
    attribute: AccountAttribute,
    tag_map: dict[int, list[int]],
) -> list[BalanceSummaryItem]:
    """Aggregate usd_equivalent amounts by the requested account attribute.

    tag_map: account_id -> list[tag_id]; only used when attribute=tags.
    """
    sums: dict[str | int | None, int] = defaultdict(int)

    for account, usd_equivalent in rows:
        if attribute == AccountAttribute.side:
            sums[account.side.value] += usd_equivalent
        elif attribute == AccountAttribute.currency:
            sums[account.currency_code] += usd_equivalent
        elif attribute == AccountAttribute.institution:
            sums[account.institution_id] += usd_equivalent
        elif attribute == AccountAttribute.tags:
            tag_ids = tag_map.get(account.id or 0, [])
            if tag_ids:
                for tag_id in tag_ids:
                    sums[tag_id] += usd_equivalent
            else:
                sums[None] += usd_equivalent

    def _sort_key(k: str | int | None) -> tuple[int, str | int]:
        if k is None:
            return (1, 0)
        return (0, k)

    return [
        BalanceSummaryItem(group_key=k, balance_sum_usd=v)
        for k, v in sorted(sums.items(), key=lambda item: _sort_key(item[0]))
    ]


def _fetch_rows_and_convert(
    account_balance_pairs: list[tuple[Account, Balance]],
    rate_lookup: dict[tuple[str, str], Decimal],
) -> list[tuple[Account, int]]:
    result: list[tuple[Account, int]] = []
    for account, balance in account_balance_pairs:
        if account.currency_code == "USD":
            usd_equivalent = balance.amount
        else:
            rate = rate_lookup[(account.currency_code, balance.month)]
            usd_equivalent = round(balance.amount / rate)
        result.append((account, usd_equivalent))
    return result


def _load_tag_map(session: Session, account_ids: list[int]) -> dict[int, list[int]]:
    if not account_ids:
        return {}
    stmt = select(AccountTag).where(
        AccountTag.account_id.in_(account_ids)  # type: ignore[union-attr]
    )
    rows = session.exec(stmt).all()
    tag_map: dict[int, list[int]] = defaultdict(list)
    for at in rows:
        if at.account_id is not None and at.tag_id is not None:
            tag_map[at.account_id].append(at.tag_id)
    return dict(tag_map)


def _check_missing_rates(
    session: Session,
    pairs: set[tuple[str, str]],
) -> dict[tuple[str, str], Decimal]:
    """Query exchange rates for the given (currency_code, month) pairs.

    Raises 422 if any pair is missing. Returns a lookup dict.
    """
    if not pairs:
        return {}
    rate_lookup: dict[tuple[str, str], Decimal] = {}
    for currency_code, month in pairs:
        stmt = select(ExchangeRate).where(
            ExchangeRate.currency_code == currency_code,
            ExchangeRate.month == month,
        )
        er = session.exec(stmt).first()
        if er is not None:
            rate_lookup[(currency_code, month)] = er.rate

    missing = [
        {"currency_code": c, "month": m}
        for c, m in sorted(pairs)
        if (c, m) not in rate_lookup
    ]
    if missing:
        raise HTTPException(
            status_code=422,
            detail={"message": "Missing exchange rates", "missing": missing},
        )
    return rate_lookup


def get_balance_summary(
    attribute: AccountAttribute,
    month: str,
    session: Session,
) -> list[BalanceSummaryItem]:
    _validate_month(month)

    stmt = (
        select(Account, Balance)
        .join(Balance, Balance.account_id == Account.id)  # type: ignore[arg-type]
        .where(Account.status == AccountStatus.active)
        .where(Balance.month == month)
    )
    pairs = session.exec(stmt).all()

    if not pairs:
        return []

    non_usd_pairs = {
        (a.currency_code, month) for a, _ in pairs if a.currency_code != "USD"
    }
    rate_lookup = _check_missing_rates(session, non_usd_pairs)

    rows = _fetch_rows_and_convert(list(pairs), rate_lookup)

    account_ids = [a.id for a, _ in pairs if a.id is not None]
    tag_map = (
        _load_tag_map(session, account_ids)
        if attribute == AccountAttribute.tags
        else {}
    )

    return _compute_groups(rows, attribute, tag_map)


def get_balance_summary_history(
    attribute: AccountAttribute,
    from_month: str,
    to_month: str | None,
    session: Session,
) -> BalanceSummaryHistoryResponse:
    _validate_month(from_month)

    if to_month is None:
        max_month = session.exec(
            select(Balance.month)
            .order_by(
                Balance.month.desc()  # type: ignore[attr-defined]
            )
            .limit(1)
        ).first()
        if max_month is None:
            return BalanceSummaryHistoryResponse(
                from_month=from_month,
                to_month=from_month,
                items=[],
            )
        to_month = max_month
    else:
        _validate_month(to_month)

    if from_month > to_month:
        raise HTTPException(
            status_code=422,
            detail=f"'from' ({from_month}) must not be after 'to' ({to_month})",
        )

    stmt = (
        select(Account, Balance)
        .join(Balance, Balance.account_id == Account.id)  # type: ignore[arg-type]
        .where(Account.status == AccountStatus.active)
        .where(Balance.month >= from_month)
        .where(Balance.month <= to_month)
    )
    all_pairs = session.exec(stmt).all()

    if not all_pairs:
        return BalanceSummaryHistoryResponse(
            from_month=from_month,
            to_month=to_month,
            items=[],
        )

    non_usd_pairs = {
        (a.currency_code, b.month) for a, b in all_pairs if a.currency_code != "USD"
    }
    rate_lookup = _check_missing_rates(session, non_usd_pairs)

    by_month: dict[str, list[tuple[Account, Balance]]] = defaultdict(list)
    for account, balance in all_pairs:
        by_month[balance.month].append((account, balance))

    account_ids = [a.id for a, _ in all_pairs if a.id is not None]
    tag_map = (
        _load_tag_map(session, account_ids)
        if attribute == AccountAttribute.tags
        else {}
    )

    items: list[BalanceSummaryHistoryItem] = []
    for month in sorted(by_month):
        rows = _fetch_rows_and_convert(by_month[month], rate_lookup)
        for summary_item in _compute_groups(rows, attribute, tag_map):
            items.append(
                BalanceSummaryHistoryItem(
                    month=month,
                    group_key=summary_item.group_key,
                    balance_sum_usd=summary_item.balance_sum_usd,
                )
            )

    return BalanceSummaryHistoryResponse(
        from_month=from_month,
        to_month=to_month,
        items=items,
    )
