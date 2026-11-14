import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from pypdf import PdfWriter
from starlette.datastructures import Headers

from app.core.config import get_settings
from app.services.file_validation_service import validate_pdf_file


def make_pdf(page_count: int = 1, password: str | None = None) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    if password:
        writer.encrypt(password)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def upload_pdf(
    content: bytes,
    filename: str | None = "document.pdf",
    content_type: str = "application/pdf",
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def validate(upload: UploadFile) -> None:
    asyncio.run(validate_pdf_file(upload))


def test_valid_pdf_restores_cursor() -> None:
    upload = upload_pdf(make_pdf())

    validate(upload)

    assert upload.file.tell() == 0


@pytest.mark.parametrize(
    ("filename", "content_type", "content", "detail"),
    [
        ("document.txt", "application/pdf", make_pdf(), "extension"),
        ("document.pdf", "text/plain", make_pdf(), "content type"),
        ("document.pdf", "application/pdf", b"not a pdf", "valid PDF"),
        (None, "application/pdf", make_pdf(), "name"),
    ],
)
def test_invalid_upload_metadata_or_signature(
    filename: str | None,
    content_type: str,
    content: bytes,
    detail: str,
) -> None:
    with pytest.raises(HTTPException, match=detail):
        validate(upload_pdf(content, filename, content_type))


def test_empty_pdf_is_rejected() -> None:
    with pytest.raises(HTTPException, match="at least one page"):
        validate(upload_pdf(make_pdf(page_count=0)))


def test_corrupted_pdf_is_rejected() -> None:
    with pytest.raises(HTTPException, match="corrupted"):
        validate(upload_pdf(b"%PDF-1.7\ninvalid content"))


def test_oversized_pdf_is_rejected() -> None:
    oversized = b"%PDF-" + b"x" * (10 * 1024 * 1024)

    with pytest.raises(HTTPException) as error:
        validate(upload_pdf(oversized))

    assert error.value.status_code == 413


def test_encrypted_pdf_is_rejected() -> None:
    with pytest.raises(HTTPException, match="Password-protected"):
        validate(upload_pdf(make_pdf(password="secret")))


def test_page_limit_is_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_PDF_PAGES", "1")
    get_settings.cache_clear()

    try:
        with pytest.raises(HTTPException, match="1-page limit"):
            validate(upload_pdf(make_pdf(page_count=2)))
    finally:
        get_settings.cache_clear()
