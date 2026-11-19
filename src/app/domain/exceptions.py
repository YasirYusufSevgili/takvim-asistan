class DomainError(Exception):
    """Tüm iş kuralı hatalarının ortak atası."""


class InvalidTimeRange(DomainError):
    """Bitiş zamanı başlangıçtan önce veya ona eşit."""


class ParsingError(DomainError):
    """Cümle anlaşılamadı ya da model geçersiz çıktı verdi."""


class LLMError(Exception):
    """AI sağlayıcısına ulaşılamadı veya boş yanıt döndü."""
