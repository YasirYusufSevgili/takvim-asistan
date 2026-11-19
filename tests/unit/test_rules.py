from datetime import date, datetime

import pytest

from app.domain.entities import Commitment, Status
from app.domain.exceptions import InvalidTimeRange
from app.domain.rules import find_conflicts, overlaps, weekly_load_hours


def make(title, start_h, end_h, day=20, status=Status.PLANNED):
    """Kasım 2026 içinde, verilen günde saat aralığı olan kayıt üretir."""
    return Commitment(
        title=title,
        start=datetime(2026, 11, day, start_h),
        end=datetime(2026, 11, day, end_h),
        status=status,
    )


def test_gecersiz_zaman_araligi_hata_verir():
    with pytest.raises(InvalidTimeRange):
        make("ters", 15, 14)


def test_bos_baslik_hata_verir():
    with pytest.raises(ValueError):
        make("  ", 10, 11)


def test_kesisen_kayitlar_cakisir():
    assert overlaps(make("a", 14, 16), make("b", 15, 17))


def test_arka_arkaya_kayitlar_cakismaz():
    assert not overlaps(make("a", 14, 15), make("b", 15, 16))


def test_baska_gundeki_kayit_cakismaz():
    assert not overlaps(make("a", 14, 16, day=20), make("b", 14, 16, day=21))


def test_find_conflicts_sadece_cakisanlari_siralayarak_dondurur():
    yeni = make("Ali'ye yardım", 14, 17)
    mevcut = [
        make("Ders", 16, 18),
        make("Spor", 9, 10),
        make("Toplantı", 13, 15),
    ]
    sonuc = find_conflicts(yeni, mevcut)
    assert [c.title for c in sonuc] == ["Toplantı", "Ders"]


def test_iptal_ve_biten_kayitlar_cakisma_sayilmaz():
    yeni = make("Yeni", 14, 16)
    mevcut = [
        make("İptal", 14, 16, status=Status.CANCELLED),
        make("Bitti", 14, 16, status=Status.DONE),
    ]
    assert find_conflicts(yeni, mevcut) == []


def test_haftalik_yuk_saat_toplar():
    mevcut = [make("a", 9, 11, day=16), make("b", 14, 17, day=20)]
    assert weekly_load_hours(mevcut, date(2026, 11, 18)) == 5.0


def test_haftalik_yuk_baska_haftayi_saymaz():
    mevcut = [make("a", 9, 11, day=16), make("b", 14, 17, day=24)]
    assert weekly_load_hours(mevcut, date(2026, 11, 18)) == 2.0
