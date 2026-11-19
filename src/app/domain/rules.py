from datetime import date, datetime, time, timedelta

from app.domain.entities import Commitment


def overlaps(a: Commitment, b: Commitment) -> bool:
    """İki kayıt zamanda kesişiyor mu? Arka arkaya olanlar çakışma sayılmaz."""
    return a.start < b.end and b.start < a.end


def find_conflicts(new: Commitment, existing: list[Commitment]) -> list[Commitment]:
    """Yeni kayıtla çakışan aktif kayıtları başlangıç saatine göre döndürür."""
    found = [c for c in existing if c.is_active and overlaps(new, c)]
    return sorted(found, key=lambda c: c.start)


def week_bounds(day: date) -> tuple[datetime, datetime]:
    """Verilen günün haftası: pazartesi 00:00 (dahil) -> sonraki pazartesi 00:00 (hariç)."""
    monday = day - timedelta(days=day.weekday())
    start = datetime.combine(monday, time.min)
    return start, start + timedelta(days=7)


def weekly_load_hours(existing: list[Commitment], day: date) -> float:
    """O hafta aktif kayıtların toplam saati. Hafta sınırını aşan kısım kesilir."""
    week_start, week_end = week_bounds(day)
    total = 0.0
    for c in existing:
        if not c.is_active:
            continue
        start = max(c.start, week_start)
        end = min(c.end, week_end)
        if start < end:
            total += (end - start).total_seconds() / 3600
    return total
