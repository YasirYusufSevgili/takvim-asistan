class DomainError(Exception):
    """Tüm iş kuralı hatalarının ortak atası."""


class InvalidTimeRange(DomainError):
    """Bitiş zamanı başlangıçtan önce veya ona eşit."""
