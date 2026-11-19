from openai import OpenAI, OpenAIError

from app.domain.exceptions import LLMError


class NvidiaLLMClient:
    """NVIDIA'nın OpenAI uyumlu API'si üzerinden dil modeli çağrısı."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=60, max_retries=0)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        # Bazı modeller 'system' rolünü desteklemez; uyumluluk için tek mesajda birleştiriyoruz.
        prompt = f"{system}\n\n---\nGirdi: {user}"
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=2000,
            )
        except OpenAIError as exc:
            raise LLMError(f"AI servisine ulaşılamadı: {exc}") from exc

        content = response.choices[0].message.content
        if not content:
            raise LLMError("Model boş yanıt döndürdü.")
        return content
