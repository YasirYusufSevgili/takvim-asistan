from datetime import datetime

from sqlalchemy.engine import Engine
from sqlmodel import Session, select

from app.domain.entities import Commitment, Kind, Status
from app.infrastructure.db.models import CommitmentRow


def _to_row(c: Commitment) -> CommitmentRow:
    return CommitmentRow(
        id=c.id,
        title=c.title,
        start_at=c.start,
        end_at=c.end,
        kind=c.kind.value,
        person=c.person,
        status=c.status.value,
    )


def _to_entity(row: CommitmentRow) -> Commitment:
    return Commitment(
        id=row.id,
        title=row.title,
        start=row.start_at,
        end=row.end_at,
        kind=Kind(row.kind),
        person=row.person,
        status=Status(row.status),
    )


class SqlCommitmentRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, commitment: Commitment) -> Commitment:
        row = _to_row(commitment)
        row.id = None  # kimliği veritabanı versin
        with Session(self._engine) as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return _to_entity(row)

    def get(self, commitment_id: int) -> Commitment | None:
        with Session(self._engine) as session:
            row = session.get(CommitmentRow, commitment_id)
            return _to_entity(row) if row else None

    def list_between(self, start: datetime, end: datetime) -> list[Commitment]:
        statement = (
            select(CommitmentRow)
            .where(CommitmentRow.start_at < end, CommitmentRow.end_at > start)
            .order_by(CommitmentRow.start_at)
        )
        with Session(self._engine) as session:
            return [_to_entity(r) for r in session.exec(statement).all()]

    def update_status(self, commitment_id: int, status: Status) -> Commitment | None:
        with Session(self._engine) as session:
            row = session.get(CommitmentRow, commitment_id)
            if row is None:
                return None
            row.status = status.value
            session.add(row)
            session.commit()
            session.refresh(row)
            return _to_entity(row)

    def delete(self, commitment_id: int) -> bool:
        with Session(self._engine) as session:
            row = session.get(CommitmentRow, commitment_id)
            if row is None:
                return False
            session.delete(row)
            session.commit()
            return True
