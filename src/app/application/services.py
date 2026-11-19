import json
from datetime import date, datetime, time, timedelta
from typing import Callable

from app.application.dto import ParseResult
from app.application.interfaces import LLMClient
from app.domain.entities import Commitment, Kind
from app.domain.exceptions import ParsingError

DAY_NAMES = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
DEFAULT_DURATION_MIN = 60

_PROMPT = """Sen bir takvim asistanının ayrıştırıcısısın. Kullanıcının Türkçe cümlesinden plan veya söz bilgisini çıkarırsın.
Şu anki zaman: __TODAY__ __DAY__, saat __CLOCK__.

Sadece geçerli bir JSON nesnesi döndür, başka hiçbir şey yazma. Alanlar:
{
  "title": kısa başlık (string) veya null,
  "person": ilgili kişi (string) veya null,
  "kind": "promise" (birine verilen söz, yardım, buluşma) veya "plan" (kullanıcının kendi işi, dersi, sporu, randevusu),
  "date": "YYYY-MM-DD" veya null,
  "time": "HH:MM" (24 saat) veya null,
  "end_time": "HH:MM" veya null,
  "duration_minutes": tamsayı veya null
}

Kurallar:
- Göreli günleri (yarın, cuma, haftaya salı) yukarıdaki bugüne göre hesapla. Gün adı söylenirse bugünden itibaren en yakın o günü seç; bugün o gün ise bugünü seç.
- Tarih söylenmediyse date null olsun. Saat söylenmediyse time null olsun. Eksik bilgiyi ASLA tahmin etme veya uydurma.
- "sabah 9" -> 09:00, "öğlen 12" -> 12:00, "öğleden sonra 3" -> 15:00, "akşam 8" -> 20:00.
- Cümle bir plan veya söz içermiyorsa title null olsun.
"""


def _clean(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return None if value.lower() in ("", "null", "none") else value


def _extract_json(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ParsingError("Model JSON döndürmedi.")
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ParsingError("Model geçersiz JSON döndürdü.") from exc
    if not isinstance(data, dict):
        raise ParsingError("Model beklenen biçimde yanıt vermedi.")
    return data


def _parse_date(value: object) -> date | None:
    text = _clean(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ParsingError(f"Geçersiz tarih: {text}") from exc


def _parse_time(value: object) -> time | None:
    text = _clean(value)
    if text is None:
        return None
    try:
        return time.fromisoformat(text)
    except ValueError as exc:
        raise ParsingError(f"Geçersiz saat: {text}") from exc


class CommitmentParser:
    """Doğal dil cümlesini Commitment'a çevirir. AI sağlayıcısından bağımsızdır."""

    def __init__(self, llm: LLMClient, now: Callable[[], datetime] = datetime.now) -> None:
        self._llm = llm
        self._now = now

    def _system_prompt(self) -> str:
        now = self._now()
        return (
            _PROMPT.replace("__TODAY__", now.date().isoformat())
            .replace("__DAY__", DAY_NAMES[now.weekday()])
            .replace("__CLOCK__", now.strftime("%H:%M"))
        )

    def parse(self, text: str) -> ParseResult:
        text = text.strip()
        if not text:
            raise ParsingError("Boş cümle.")

        data = _extract_json(self._llm.complete(self._system_prompt(), text))

        title = _clean(data.get("title"))
        person = _clean(data.get("person"))
        kind = Kind.PLAN if data.get("kind") == "plan" else Kind.PROMISE
        day = _parse_date(data.get("date"))
        start_time = _parse_time(data.get("time"))

        missing = []
        if not title:
            missing.append("başlık")
        if day is None:
            missing.append("tarih")
        if start_time is None:
            missing.append("saat")
        if missing:
            question = f"Şu bilgi eksik: {', '.join(missing)}. Ekleyebilir misin?"
            return ParseResult(commitment=None, missing=tuple(missing), question=question)

        start = datetime.combine(day, start_time)
        end = self._resolve_end(start, data)
        commitment = Commitment(title=title, start=start, end=end, kind=kind, person=person)
        return ParseResult(commitment=commitment)

    @staticmethod
    def _resolve_end(start: datetime, data: dict) -> datetime:
        end_time = _parse_time(data.get("end_time"))
        if end_time is not None:
            end = datetime.combine(start.date(), end_time)
            if end <= start:
                raise ParsingError("Bitiş saati başlangıçtan sonra olmalı.")
            return end

        minutes = data.get("duration_minutes")
        if isinstance(minutes, (int, float)) and not isinstance(minutes, bool) and minutes > 0:
            return start + timedelta(minutes=minutes)
        return start + timedelta(minutes=DEFAULT_DURATION_MIN)
