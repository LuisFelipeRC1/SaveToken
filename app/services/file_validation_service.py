
from io import BytesIO

from fastapi import HTTPException, UploadFile  # type: ignore
from pypdf import PdfReader

from app.core.config import get_settings


MAX_PDF_SIZE_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 1_000
READ_CHUNK_SIZE = 64 * 1024


async def validate_pdf_file(pdf: UploadFile) -> None:
    """Validate the uploaded PDF without leaving the file cursor advanced."""

    try:
        settings = get_settings()
        max_pdf_size_bytes = settings.max_pdf_size_bytes
        max_pdf_pages = settings.max_pdf_pages

        if not pdf.filename:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file must have a name.",
            )

        if not pdf.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Only files with a .pdf extension are supported.",
            )

        if pdf.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="The uploaded file must use the application/pdf content type.",
            )

        pdf_bytes = bytearray()
        while True:
            chunk = await pdf.read(READ_CHUNK_SIZE)
            if not chunk:
                break

            pdf_bytes.extend(chunk)
            if len(pdf_bytes) > max_pdf_size_bytes:
                raise HTTPException(
                    status_code=413,
                    detail="The PDF exceeds the 10 MiB size limit.",
                )

        if len(pdf_bytes) < 5 or bytes(pdf_bytes[:5]) != b"%PDF-":
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid PDF.",
            )

        try:
            reader = PdfReader(BytesIO(pdf_bytes), strict=False)
            if reader.is_encrypted:
                try:
                    decrypted = reader.decrypt("")
                except Exception as exc:
                    raise HTTPException(
                        status_code=400,
                        detail="Password-protected PDFs are not supported.",
                    ) from exc

                if not decrypted:
                    raise HTTPException(
                        status_code=400,
                        detail="Password-protected PDFs are not supported.",
                    )

            page_count = len(reader.pages)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="The PDF is corrupted or cannot be interpreted.",
            ) from exc

        if page_count == 0:
            raise HTTPException(
                status_code=400,
                detail="The PDF must contain at least one page.",
            )

        if page_count > max_pdf_pages:
            raise HTTPException(
                status_code=400,
                detail=f"The PDF exceeds the {max_pdf_pages}-page limit.",
            )
    finally:
        await pdf.seek(0)
