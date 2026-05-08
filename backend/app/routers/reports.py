import logging

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.models.report import (
    AccountAttribute,
    BalanceSummaryHistoryResponse,
    BalanceSummaryItem,
)
from app.services.reports import get_balance_summary, get_balance_summary_history

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reports"])


@router.get("/reports/balance-summary", response_model=list[BalanceSummaryItem])
def balance_summary(
    attribute: AccountAttribute,
    month: str,
    session: Session = Depends(get_session),
) -> list[BalanceSummaryItem]:
    return get_balance_summary(attribute, month, session)


@router.get(
    "/reports/balance-summary/history",
    response_model=BalanceSummaryHistoryResponse,
)
def balance_summary_history(
    attribute: AccountAttribute,
    from_: str = Query(alias="from"),
    to: str | None = None,
    session: Session = Depends(get_session),
) -> BalanceSummaryHistoryResponse:
    return get_balance_summary_history(attribute, from_, to, session)
