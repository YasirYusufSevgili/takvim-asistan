import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.getenv("NVIDIA_API_KEY")
if not key:
    raise SystemExit("NVIDIA_API_KEY bulunamadı. .env dosyasını kontrol et.")

client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key)
modeller = sorted(m.id for m in client.models.list().data)
print(f"{len(modeller)} model bulundu. Bazıları:\n")
for m in modeller:
    if any(k in m.lower() for k in ["instruct", "llama", "qwen", "gemma", "mistral", "deepseek", "gpt-oss", "kimi", "glm", "minimax"]):
        print(m)
