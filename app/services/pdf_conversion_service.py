
from io import BytesIO
from dataclasses import dataclass


class PDFConversionError(RuntimeError):
    """Raised when Docling cannot produce Markdown from the uploaded PDF."""


@dataclass(frozen=True)
class PDFConversionResult:
    document: object
    faithful_markdown: str


def convert_pdf_to_document(pdf_bytes: bytes, filename: str) -> PDFConversionResult:
    if not pdf_bytes:
        raise PDFConversionError("The PDF content is empty.")

    document_name = _safe_document_name(filename)

    try:
        from docling.datamodel.base_models import DocumentStream
        from docling.document_converter import DocumentConverter

        converter = DocumentConverter()
        source = DocumentStream(
            name=document_name,
            stream=BytesIO(pdf_bytes),
        )
        result = converter.convert(source)
    except Exception as exc:
        raise PDFConversionError("Docling failed to convert the PDF.") from exc

    status = getattr(result, "status", None)
    if status is not None:
        status_value = getattr(status, "value", status)
        if str(status_value).lower() in {"failure", "failed", "error"}:
            raise PDFConversionError("Docling reported a failed PDF conversion.")

    document = getattr(result, "document", None)
    if document is None:
        raise PDFConversionError("Docling returned no document.")

    try:
        markdown = document.export_to_markdown()
    except Exception as exc:
        raise PDFConversionError("Docling failed to export Markdown.") from exc

    if not isinstance(markdown, str) or not markdown.strip():
        raise PDFConversionError("Docling returned an empty Markdown document.")

    return PDFConversionResult(document=document, faithful_markdown=markdown)


def convert_pdf_to_markdown(pdf_bytes: bytes, filename: str) -> str:
    """Convert a PDF and return the faithful Markdown export."""

    return convert_pdf_to_document(pdf_bytes, filename).faithful_markdown


def _safe_document_name(filename: str) -> str:
    """Keep only a display name; never treat client input as a filesystem path."""

    normalized_name = (filename or "document.pdf").strip().replace("\\", "/")
    document_name = normalized_name.rsplit("/", maxsplit=1)[-1]

    return document_name or "document.pdf"
