from sqlmodel import Field, SQLModel


class Currency(SQLModel, table=True):
    code: str = Field(primary_key=True)
    name: str
