from decimal import Decimal
from typing import Any, ClassVar, Optional, Tuple

from sqlalchemy import Column, Numeric, UniqueConstraint
from sqlmodel import Field, SQLModel


class ExchangeRate(SQLModel, table=True):
    __table_args__: ClassVar[Tuple[Any, ...]] = (
        UniqueConstraint("currency_code", "month"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    currency_code: str = Field(foreign_key="currency.code")
    month: str  # YYYY-MM
    rate: Decimal = Field(sa_column=Column(Numeric(10, 4), nullable=False))
