from datetime import datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


class CommitmentRow(SQLModel, table=True):
    __tablename__ = "commitments"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    # Saat dilimsiz (naive) saklıyoruz: kullanıcının yerel saati olarak.
    start_at: datetime = Field(sa_type=DateTime, index=True)
    end_at: datetime = Field(sa_type=DateTime)
    kind: str
    person: str | None = None
    status: str
