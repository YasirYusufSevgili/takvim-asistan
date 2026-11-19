import time

from openai import OpenAI, OpenAIError

from app.core.config import load_settings

ADAYLAR = [
    "google/gemma-3-4b-it",
    "google/gemma-3-12b-it",
    "z-ai/glm-5.3-flash",
    "minimaxai/minimax-m3.1-flash",
    "google/gemma-4-31b-it",
]

s = load_settings()
client = OpenAI(base_url=s.nvidia_base_url, api_key=s.nvidia_api_key, timeout=20, max_retries=0)

for model in ADAYLAR:
    t0 = time.time()
    try:
        r = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Sadece 'merhaba' yaz."}],
            max_tokens=20,
        )
        yanit = (r.choices[0].message.content or "").strip().replace("\n", " ")
        print(f"OK     {time.time() - t0:5.1f} sn  {model}  -> {yanit[:40]}")
    except OpenAIError as exc:
        print(f"HATA   {time.time() - t0:5.1f} sn  {model}  -> {str(exc)[:70]}")
