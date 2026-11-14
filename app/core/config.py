from dataclasses import dataclass
from functools import lru_cache
import os


def _read_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default

    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc

    if parsed < 1:
        raise ValueError(f"{name} must be greater than zero.")
    return parsed


@dataclass(frozen=True)
class Settings:
    max_pdf_size_mb: int = 10
    max_pdf_pages: int = 1_000
    max_concurrent_conversions: int = 1
    tokenizer_encoding: str = "cl100k_base"
    cors_allowed_origins: tuple[str, ...] = (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )

    @property
    def max_pdf_size_bytes(self) -> int:
        return self.max_pdf_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    )

    return Settings(
        max_pdf_size_mb=_read_int("MAX_PDF_SIZE_MB", 10),
        max_pdf_pages=_read_int("MAX_PDF_PAGES", 1_000),
        max_concurrent_conversions=_read_int("MAX_CONCURRENT_CONVERSIONS", 1),
        tokenizer_encoding=os.getenv("TOKENIZER_ENCODING", "cl100k_base").strip()
        or "cl100k_base",
        cors_allowed_origins=origins,
    )
