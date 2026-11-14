import asyncio
from dataclasses import dataclass
from typing import Literal

from fastapi import UploadFile  # type: ignore
from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.services.file_validation_service import validate_pdf_file
from app.services.markdown_optimization_service import select_optimized_markdown
from app.services.pdf_conversion_service import convert_pdf_to_document
from app.services.token_count_service import TokenMetrics, calculate_token_metrics


ConversionMode = Literal["faithful", "optimized"]
MAX_CONCURRENT_CONVERSIONS = get_settings().max_concurrent_conversions
_conversion_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CONVERSIONS)


@dataclass(frozen=True)
class ConversionResult:
    filename: str
    mode: ConversionMode
    markdown_content: str
    faithful_markdown: str
    token_metrics: TokenMetrics


async def convert_document(
    pdf: UploadFile,
    mode: ConversionMode = "faithful",
) -> ConversionResult:
    """Coordinate validation, conversion, optimization and token metrics."""

    async with _conversion_semaphore:
        await validate_pdf_file(pdf)
        pdf_bytes = await pdf.read()
        filename = pdf.filename or "document.pdf"

        conversion = await run_in_threadpool(
            convert_pdf_to_document,
            pdf_bytes,
            filename,
        )
        faithful_markdown = conversion.faithful_markdown

        if mode == "optimized":
            markdown_content, token_metrics = await run_in_threadpool(
                select_optimized_markdown,
                conversion.document,
                faithful_markdown,
                get_settings().tokenizer_encoding,
            )
        else:
            markdown_content = faithful_markdown
            token_metrics = await run_in_threadpool(
                calculate_token_metrics,
                faithful_markdown,
                markdown_content,
                get_settings().tokenizer_encoding,
            )

        return ConversionResult(
            filename=filename,
            mode=mode,
            markdown_content=markdown_content,
            faithful_markdown=faithful_markdown,
            token_metrics=token_metrics,
        )
