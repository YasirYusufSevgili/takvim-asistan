from dataclasses import dataclass

from app.domain.entities import Commitment


@dataclass(frozen=True)
class ParseResult:
    """Ayrıştırma sonucu: ya tam kayıt, ya da eksik bilgi ve kullanıcıya soru."""

    commitment: Commitment | None
    missing: tuple[str, ...] = ()
    question: str | None = None

    @property
    def is_complete(self) -> bool:
        return self.commitment is not None
