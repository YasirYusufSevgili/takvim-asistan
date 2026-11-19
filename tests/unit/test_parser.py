from datetime import datetime, timedelta

import pytest

from app.application.services import CommitmentParser
from app.domain.entities import Kind
from app.domain.exceptions import ParsingError

NOW = datetime(2026, 11, 20, 14, 30)  # Cuma


class FakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def complete(self, system, user):
        self.calls.append((system, user))
        return self.reply


def make_parser(reply):
    llm = FakeLLM(reply)
    return CommitmentParser(llm, now=lambda: NOW), llm


TAM = (
    '{"title": "Sunum yardımı", "person": "Ali", "kind": "promise", '
    '"date": "2026-11-27", "time": "15:00", "end_time": null, "duration_minutes": null}'
)


def test_tam_cumle_kayda_donusur():
    parser, _ = make_parser(TAM)
    sonuc = parser.parse("Cuma Ali'ye sunum yardımı 3'te")
    assert sonuc.is_complete
    c = sonuc.commitment
    assert c.title == "Sunum yardımı"
    assert c.person == "Ali"
    assert c.kind == Kind.PROMISE
    assert c.start == datetime(2026, 11, 27, 15, 0)


def test_sure_belirtilmezse_bir_saat_varsayilir():
    parser, _ = make_parser(TAM)
    c = parser.parse("x").commitment
    assert c.end - c.start == timedelta(hours=1)


def test_duration_minutes_kullanilir():
    reply = TAM.replace('"duration_minutes": null', '"duration_minutes": 90')
    parser, _ = make_parser(reply)
    c = parser.parse("x").commitment
    assert c.end - c.start == timedelta(minutes=90)


def test_end_time_kullanilir():
    reply = TAM.replace('"end_time": null', '"end_time": "17:30"')
    parser, _ = make_parser(reply)
    c = parser.parse("x").commitment
    assert c.end == datetime(2026, 11, 27, 17, 30)


def test_bitis_baslangictan_once_ise_hata():
    reply = TAM.replace('"end_time": null', '"end_time": "14:00"')
    parser, _ = make_parser(reply)
    with pytest.raises(ParsingError):
        parser.parse("x")


def test_saat_yoksa_eksik_bilgi_sorusu_doner():
    reply = TAM.replace('"time": "15:00"', '"time": null')
    parser, _ = make_parser(reply)
    sonuc = parser.parse("Cuma Ali'ye sunum yardımı")
    assert not sonuc.is_complete
    assert sonuc.commitment is None
    assert sonuc.missing == ("saat",)
    assert "saat" in sonuc.question


def test_birden_fazla_eksik_hepsi_listelenir():
    parser, _ = make_parser('{"title": null, "date": null, "time": null}')
    sonuc = parser.parse("selam")
    assert sonuc.missing == ("başlık", "tarih", "saat")


def test_markdown_icindeki_json_kabul_edilir():
    parser, _ = make_parser("```json\n" + TAM + "\n```")
    assert parser.parse("x").is_complete


def test_model_metin_donerse_hata():
    parser, _ = make_parser("Üzgünüm, anlayamadım.")
    with pytest.raises(ParsingError):
        parser.parse("x")


def test_gecersiz_tarih_hata_verir():
    parser, _ = make_parser(TAM.replace("2026-11-27", "yarın"))
    with pytest.raises(ParsingError):
        parser.parse("x")


def test_bos_cumle_hata_verir():
    parser, llm = make_parser(TAM)
    with pytest.raises(ParsingError):
        parser.parse("   ")
    assert llm.calls == []  # boş cümle için modele gidilmez


def test_prompta_bugunun_tarihi_ve_gunu_verilir():
    parser, llm = make_parser(TAM)
    parser.parse("x")
    system, _ = llm.calls[0]
    assert "2026-11-20" in system
    assert "Cuma" in system
    assert "14:30" in system
