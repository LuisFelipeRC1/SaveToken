import re
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, File, Form, Response, UploadFile

from app.schemas.conversion import ConversionMode
from app.services.conversion_service import convert_document


router = APIRouter(tags=["conversion"])


@router.post(
    "/api/v1/conversions",
    response_class=Response,
    summary="Convert a PDF document to Markdown",
    responses={
        200: {
            "description": "The converted Markdown file.",
            "content": {"text/markdown": {}},
        },
        400: {"description": "Invalid PDF."},
        413: {"description": "The PDF exceeds the configured size limit."},
        422: {"description": "Invalid request parameters."},
        500: {"description": "The PDF conversion failed."},
    },
)
@router.post("/convert", response_class=Response, include_in_schema=False)
async def convert_pdf_endpoint(
    pdf: Annotated[
        UploadFile,
        File(description="PDF file to convert"),
    ],
    mode: Annotated[
        ConversionMode,
        Form(description="faithful preserves the export; optimized applies safe whitespace cleanup."),
    ] = "faithful",
) -> Response:
    result = await convert_document(pdf, mode)
    download_name = _markdown_download_name(result.filename)
    ascii_name = download_name.encode("ascii", errors="ignore").decode() or "document.md"

    response = Response(
        content=result.markdown_content,
        media_type="text/markdown",
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{ascii_name}"; '
        f"filename*=UTF-8''{quote(download_name)}"
    )
    response.headers["X-SaveToken-Mode"] = result.mode
    response.headers["X-SaveToken-Tokenizer"] = result.token_metrics.tokenizer
    response.headers["X-SaveToken-Tokens-Before"] = str(result.token_metrics.tokens_before)
    response.headers["X-SaveToken-Tokens-After"] = str(result.token_metrics.tokens_after)
    response.headers["X-SaveToken-Token-Difference"] = str(
        result.token_metrics.token_difference
    )
    response.headers["X-SaveToken-Reduction-Percentage"] = (
        f"{result.token_metrics.reduction_percentage:.6f}"
    )
    return response


def _markdown_download_name(filename: str) -> str:
    normalized = (filename or "document.pdf").replace("\\", "/")
    basename = normalized.rsplit("/", maxsplit=1)[-1]
    stem = re.sub(r"(?i)\.pdf$", "", basename) or "document"
    safe_stem = re.sub(r'[\x00-\x1f\x7f"/\\<>:|?*]+', "_", stem).strip(" .")
    return f"{safe_stem or 'document'}.md"
