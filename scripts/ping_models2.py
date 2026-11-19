import time

from openai import OpenAI, OpenAIError

from app.core.config import load_settings

ADAYLAR = [
    "minimaxai/minimax-m3.1-flash",
    "mistralai/mistral-large-4-1t-a52b",
    "moonshotai/kimi-k3.1-pro",
]
PROMPT = (
    'Şu cümleyi JSON\'a çevir, sadece JSON yaz: "yarın 15:00\'te Ayşe ile kahve". '
    'Alanlar: title, person, date (YYYY-MM-DD), time (HH:MM). Bugün 2026-11-20 Cuma.'
)

s = load_settings()
client = OpenAI(base_url=s.nvidia_base_url, api_key=s.nvidia_api_key, timeout=40, max_retries=0)

for model in ADAYLAR:
    t0 = time.time()
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": PROMPT}],
            max_tokens=800,
            temperature=0,
        )
        m = r.choices[0].message
        icerik = (m.content or "").strip().replace("\n", " ")
        dusunme = bool(getattr(m, "reasoning_content", None))
        print(f"OK    {time.time() - t0:5.1f} sn  {model}")
        print(f"      bitiş: {r.choices[0].finish_reason} | düşünme alanı: {dusunme}")
        print(f"      içerik: {icerik[:150] or '(BOŞ)'}\n")
    except OpenAIError as exc:
        print(f"HATA  {time.time() - t0:5.1f} sn  {model} -> {str(exc)[:80]}\n")
