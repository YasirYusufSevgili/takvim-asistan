from datetime import datetime

import pytest

from app.application.assistant import PromiseAssistant
from app.application.services import CommitmentParser
from app.domain.entities import Commitment, Kind, Status
from app.domain.exceptions import LLMError

NOW = datetime(2026, 11, 20, 14, 30)

PARSE_REPLY = (
    '{"title": "Sunum yardımı", "person": "Ali", "kind": "promise", '
    '"date": "2026-11-24", "time": "15:00", "end_time": null, "duration_minutes": null}'
)


class FakeLLM:
    """Ayrıştırma istenirse JSON, ret mesajı istenirse düz metin döndürür."""

    def __init__(self, decline_reply="Bugün başka işim var, yarın olur mu?"):
        self.decline_reply = decline_reply
        self.decline_inputs = []

    def complete(self, system, user):
        if "ayrıştırıcı" in system:
            return PARSE_REPLY
        self.decline_inputs.append(user)
        return self.decline_reply


def ders(status=Status.PLANNED):
    return Commitment(
        title="Ders",
        start=datetime(2026, 11, 24, 14, 0),
        end=datetime(2026, 11, 24, 16, 0),
        kind=Kind.PLAN,
        status=status,
    )


def make_assistant(repo, llm=None):
    llm = llm or FakeLLM()
    parser = CommitmentParser(llm, now=lambda: NOW)
    return PromiseAssistant(repo, llm, parser), llm


def test_cakisma_bulunur(repo):
    repo.add(ders())
    assistant, _ = make_assistant(repo)
    sonuc = assistant.evaluate("haftaya salı 15:00 Ali'ye sunum yardımı")
    assert sonuc.has_conflict
    assert [c.title for c in sonuc.conflicts] == ["Ders"]


def test_cakisma_yoksa_bos_doner(repo):
    assistant, _ = make_assistant(repo)
    sonuc = assistant.evaluate("x")
    assert not sonuc.needs_info
    assert not sonuc.has_conflict


def test_iptal_edilen_kayit_cakisma_sayilmaz(repo):
    repo.add(ders(status=Status.CANCELLED))
    assistant, _ = make_assistant(repo)
    assert not assistant.evaluate("x").has_conflict


def test_haftalik_yuk_yeni_kaydi_da_icerir(repo):
    repo.add(ders())  # 2 saat
    assistant, _ = make_assistant(repo)
    assert assistant.evaluate("x").weekly_load == 3.0  # 2 saat + yeni 1 saat


def test_eksik_bilgide_cakisma_aranmaz(repo):
    class EksikLLM(FakeLLM):
        def complete(self, system, user):
            return '{"title": "Sunum", "date": "2026-11-24", "time": null}'

    repo.add(ders())
    assistant, _ = make_assistant(repo, EksikLLM())
    sonuc = assistant.evaluate("x")
    assert sonuc.needs_info
    assert sonuc.conflicts == ()


def test_onayla_veritabanina_kaydeder(repo):
    assistant, _ = make_assistant(repo)
    yeni = assistant.evaluate("x").parse.commitment
    kayit = assistant.confirm(yeni)
    assert kayit.id is not None
    assert repo.get(kayit.id).title == "Sunum yardımı"


def test_ret_mesaji_uretilir_ve_baglam_modele_gider(repo):
    repo.add(ders())
    assistant, llm = make_assistant(repo)
    sonuc = assistant.evaluate("x")
    mesaj = assistant.draft_decline(sonuc.parse.commitment, sonuc.conflicts)
    assert mesaj == "Bugün başka işim var, yarın olur mu?"
    girdi = llm.decline_inputs[0]
    assert "Ders" in girdi and "Ali" in girdi


def test_bos_ret_mesaji_hata_verir(repo):
    repo.add(ders())
    assistant, _ = make_assistant(repo, FakeLLM(decline_reply="   "))
    sonuc = assistant.evaluate("x")
    with pytest.raises(LLMError):
        assistant.draft_decline(sonuc.parse.commitment, sonuc.conflicts)
