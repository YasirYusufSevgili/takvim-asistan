import time

from app.application.services import CommitmentParser
from app.core.config import load_settings
from app.domain.exceptions import DomainError, LLMError
from app.infrastructure.clients import NvidiaLLMClient

CUMLELER = [
    "Cuma Ali'ye sunum yardımı",
    "yarın 15:00'te Ayşe ile kahve",
    "Pazartesi sabah 9da dişçi randevum var, 1 saat sürer",
    "bugün akşam 8'de maç",
    "haftaya salı 14:00-16:00 proje toplantısı",
    "selam nasılsın",
]

settings = load_settings()
if not settings.nvidia_api_key:
    raise SystemExit("NVIDIA_API_KEY bulunamadı.")

print(f"Model: {settings.nvidia_model}\n")
llm = NvidiaLLMClient(settings.nvidia_api_key, settings.nvidia_model, settings.nvidia_base_url)
parser = CommitmentParser(llm)

for cumle in CUMLELER:
    print(f"> {cumle}")
    t0 = time.time()
    try:
        sonuc = parser.parse(cumle)
        if sonuc.is_complete:
            c = sonuc.commitment
            print(f"  OK  [{c.kind.value}] {c.title} | kişi: {c.person} | {c.start:%d.%m %H:%M} -> {c.end:%H:%M}")
        else:
            print(f"  EKSİK  {sonuc.question}")
    except (DomainError, LLMError) as exc:
        print(f"  HATA  {exc}")
    print(f"  ({time.time() - t0:.1f} sn)\n")
