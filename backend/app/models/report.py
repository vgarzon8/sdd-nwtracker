from enum import Enum

from pydantic import BaseModel


class AccountAttribute(str, Enum):
    side = "side"
    currency = "currency"
    institution = "institution"
    tags = "tags"


class BalanceSummaryItem(BaseModel):
    group_key: str | int | None
    balance_sum_usd: int


class BalanceSummaryHistoryItem(BaseModel):
    month: str
    group_key: str | int | None
    balance_sum_usd: int


class BalanceSummaryHistoryResponse(BaseModel):
    from_month: str
    to_month: str
    items: list[BalanceSummaryHistoryItem]
