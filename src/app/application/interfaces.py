from datetime import datetime
from typing import Protocol

from app.domain.entities import Commitment, Status


class CommitmentRepository(Protocol):
    def add(self, commitment: Commitment) -> Commitment: ...

    def get(self, commitment_id: int) -> Commitment | None: ...

    def list_between(self, start: datetime, end: datetime) -> list[Commitment]:
        """Verilen aralıkla kesişen tüm kayıtlar, başlangıca göre sıralı."""
        ...

    def update_status(self, commitment_id: int, status: Status) -> Commitment | None: ...

    def delete(self, commitment_id: int) -> bool: ...


class LLMClient(Protocol):
    """Herhangi bir dil modeli sağlayıcısı (NVIDIA, Gemini, Claude...) bunu uygular."""

    def complete(self, system: str, user: str) -> str: ...
