from typing import Any, ClassVar, Optional, Tuple

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Balance(SQLModel, table=True):
    __table_args__: ClassVar[Tuple[Any, ...]] = (
        UniqueConstraint("account_id", "month"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id")
    month: str  # YYYY-MM
    amount: int
