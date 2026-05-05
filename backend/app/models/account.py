from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class AccountSide(str, Enum):
    asset = "asset"
    liability = "liability"


class AccountStatus(str, Enum):
    active = "active"
    closed = "closed"


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    institution_id: int = Field(foreign_key="institution.id")
    currency_code: str = Field(foreign_key="currency.code")
    side: AccountSide
    status: AccountStatus


class AccountTag(SQLModel, table=True):
    account_id: Optional[int] = Field(
        default=None, foreign_key="account.id", primary_key=True
    )
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)
