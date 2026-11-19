from dataclasses import dataclass

from app.application.dto import ParseResult
from app.application.interfaces import CommitmentRepository, LLMClient
from app.application.services import CommitmentParser
from app.domain.entities import Commitment
from app.domain.exceptions import LLMError
from app.domain.rules import find_conflicts, week_bounds, weekly_load_hours

_DECLINE_PROMPT = """Sen bir mesaj yazım asistanısın. Kullanıcı birine "evet" demeden önce takvimine baktı ve çakışma buldu.
Kullanıcı adına, karşı tarafa gönderilecek KISA (en fazla 3 cümle) bir Türkçe mesaj yaz.
Mesaj kibar olsun, mazeret olarak kullanıcının o saatte başka işi olduğunu söylesin ve başka bir zaman önersin.
Üslup: __TONE__.
Sadece mesajın kendisini yaz. Açıklama, tırnak işareti veya başlık ekleme."""


@dataclass(frozen=True)
class Evaluation:
    """Bir cümlenin değerlendirme sonucu."""

    parse: ParseResult
    conflicts: tuple[Commitment, ...] = ()
    weekly_load: float = 0.0  # yeni kayıt dahil, o haftanın toplam saati

    @property
    def needs_info(self) -> bool:
        return not self.parse.is_complete

    @property
    def has_conflict(self) -> bool:
        return bool(self.conflicts)


class PromiseAssistant:
    """Cümleyi anlar, haftana bakar, çakışmayı bulur, ret mesajı yazar."""

    def __init__(
        self,
        repo: CommitmentRepository,
        llm: LLMClient,
        parser: CommitmentParser,
    ) -> None:
        self._repo = repo
        self._llm = llm
        self._parser = parser

    def evaluate(self, text: str) -> Evaluation:
        result = self._parser.parse(text)
        if not result.is_complete:
            return Evaluation(parse=result)

        new = result.commitment
        overlapping = self._repo.list_between(new.start, new.end)
        conflicts = find_conflicts(new, overlapping)

        day = new.start.date()
        week_start, week_end = week_bounds(day)
        week_items = self._repo.list_between(week_start, week_end)
        load = weekly_load_hours(week_items + [new], day)

        return Evaluation(parse=result, conflicts=tuple(conflicts), weekly_load=load)

    def confirm(self, commitment: Commitment) -> Commitment:
        """Kullanıcı onayladı: kaydı veritabanına yazar (çakışma olsa bile, karar kullanıcının)."""
        return self._repo.add(commitment)

    def draft_decline(
        self,
        new: Commitment,
        conflicts: tuple[Commitment, ...],
        tone: str = "samimi ve sıcak",
    ) -> str:
        system = _DECLINE_PROMPT.replace("__TONE__", tone)
        lines = [f"Gelen istek: {new.title}"]
        if new.person:
            lines.append(f"İsteyen kişi: {new.person}")
        lines.append(f"İstenen zaman: {new.start:%d.%m.%Y %H:%M}-{new.end:%H:%M}")
        lines.append("Kullanıcının o saatteki işleri:")
        for c in conflicts:
            lines.append(f"- {c.title} ({c.start:%H:%M}-{c.end:%H:%M})")

        message = self._llm.complete(system, "\n".join(lines)).strip().strip('"').strip()
        if not message:
            raise LLMError("Model boş mesaj döndürdü.")
        return message
