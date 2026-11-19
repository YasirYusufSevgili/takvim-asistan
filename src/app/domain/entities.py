from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.domain.exceptions import InvalidTimeRange


class Kind(str, Enum):
    PLAN = "plan"        # kendi planım (ders, spor, çalışma)
    PROMISE = "promise"  # birine verdiğim söz


class Status(str, Enum):
    PLANNED = "planned"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Commitment:
    """Takvimde zaman kaplayan bir plan ya da söz."""

    title: str
    start: datetime
    end: datetime
    kind: Kind = Kind.PROMISE
    person: str | None = None
    status: Status = Status.PLANNED
    id: int | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Başlık boş olamaz.")
        if self.end <= self.start:
            raise InvalidTimeRange("Bitiş, başlangıçtan sonra olmalı.")

    @property
    def is_active(self) -> bool:
        """Sadece 'planlandı' durumundakiler takvimde yer tutar."""
        return self.status == Status.PLANNED

    @property
    def duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600
