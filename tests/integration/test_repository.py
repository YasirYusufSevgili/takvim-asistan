from datetime import date, datetime

from app.domain.entities import Commitment, Kind, Status
from app.domain.rules import find_conflicts, week_bounds


def make(title, start_h, end_h, day=20, **kw):
    return Commitment(
        title=title,
        start=datetime(2026, 11, day, start_h),
        end=datetime(2026, 11, day, end_h),
        **kw,
    )


def test_ekle_ve_getir(repo):
    kayit = repo.add(make("Ali'ye yardım", 14, 16, person="Ali", kind=Kind.PROMISE))
    assert kayit.id is not None

    geri = repo.get(kayit.id)
    assert geri == kayit
    assert geri.person == "Ali"
    assert geri.kind == Kind.PROMISE


def test_olmayan_kayit_none_doner(repo):
    assert repo.get(999) is None


def test_aralik_sorgusu_sadece_kesisenleri_getirir(repo):
    repo.add(make("Bu hafta", 10, 11, day=18))
    repo.add(make("Sonraki hafta", 10, 11, day=25))
    start, end = week_bounds(date(2026, 11, 18))

    sonuc = repo.list_between(start, end)
    assert [c.title for c in sonuc] == ["Bu hafta"]


def test_aralik_sorgusu_baslangica_gore_siralar(repo):
    repo.add(make("Akşam", 18, 19))
    repo.add(make("Sabah", 8, 9))
    start, end = week_bounds(date(2026, 11, 20))
    assert [c.title for c in repo.list_between(start, end)] == ["Sabah", "Akşam"]


def test_durum_guncelle(repo):
    kayit = repo.add(make("Toplantı", 10, 11))
    guncel = repo.update_status(kayit.id, Status.CANCELLED)
    assert guncel.status == Status.CANCELLED
    assert repo.get(kayit.id).status == Status.CANCELLED


def test_olmayan_kaydin_durumu_guncellenemez(repo):
    assert repo.update_status(999, Status.DONE) is None


def test_sil(repo):
    kayit = repo.add(make("Silinecek", 10, 11))
    assert repo.delete(kayit.id) is True
    assert repo.get(kayit.id) is None
    assert repo.delete(kayit.id) is False


def test_veritabanindan_gelen_kayitla_cakisma_bulunur(repo):
    """Mantık katmanı + veritabanı birlikte: asıl senaryomuz."""
    repo.add(make("Ders", 14, 16, kind=Kind.PLAN))
    start, end = week_bounds(date(2026, 11, 20))
    yeni = make("Ali'ye yardım", 15, 17)

    cakisanlar = find_conflicts(yeni, repo.list_between(start, end))
    assert [c.title for c in cakisanlar] == ["Ders"]
