import time
from datetime import datetime

from app.application.assistant import PromiseAssistant
from app.application.services import CommitmentParser
from app.core.config import load_settings
from app.domain.entities import Commitment, Kind
from app.domain.exceptions import DomainError, LLMError
from app.infrastructure.clients import NvidiaLLMClient
from app.infrastructure.db.session import init_db, make_engine
from app.infrastructure.repositories import SqlCommitmentRepository

s = load_settings()
if not s.nvidia_api_key:
    raise SystemExit("NVIDIA_API_KEY bulunamadı.")

engine = make_engine("sqlite://")  # geçici, bellek içi
init_db(engine)
repo = SqlCommitmentRepository(engine)

# Salı gününe iki plan koyuyoruz
repo.add(Commitment("Ders", datetime(2026, 11, 24, 14), datetime(2026, 11, 24, 16), Kind.PLAN))
repo.add(Commitment("Spor", datetime(2026, 11, 24, 18), datetime(2026, 11, 24, 19), Kind.PLAN))

llm = NvidiaLLMClient(s.nvidia_api_key, s.nvidia_model, s.nvidia_base_url)
parser = CommitmentParser(llm, now=lambda: datetime(2026, 11, 20, 14, 30))
assistant = PromiseAssistant(repo, llm, parser)

cumle = "haftaya salı 15:00'te Ali'ye sunum yardımı"
print(f"Plan: salı 14-16 Ders, 18-19 Spor\n> {cumle}\n")

t0 = time.time()
try:
    sonuc = assistant.evaluate(cumle)
    print(f"Ayrıştırma + kontrol: {time.time() - t0:.1f} sn")
    if sonuc.needs_info:
        print("EKSİK:", sonuc.parse.question)
    elif sonuc.has_conflict:
        print("UYARI: Çakışma var!")
        for c in sonuc.conflicts:
            print(f"  - {c.title} ({c.start:%H:%M}-{c.end:%H:%M})")
        print(f"  Bu haftaki toplam yük: {sonuc.weekly_load:.1f} saat\n")
        t1 = time.time()
        mesaj = assistant.draft_decline(sonuc.parse.commitment, sonuc.conflicts)
        print(f"Ret mesajı taslağı ({time.time() - t1:.1f} sn):\n{mesaj}")
    else:
        print("Çakışma yok, kaydedilebilir.")
except (DomainError, LLMError) as exc:
    print("HATA:", exc)
