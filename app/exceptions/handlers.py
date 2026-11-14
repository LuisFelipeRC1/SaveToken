from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.pdf_conversion_service import PDFConversionError


async def pdf_conversion_error_handler(
    request: Request,
    exc: PDFConversionError,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "The PDF could not be converted to Markdown."},
    )


async def unexpected_error_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal error occurred."},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PDFConversionError, pdf_conversion_error_handler)
    app.add_exception_handler(Exception, unexpected_error_handler)
