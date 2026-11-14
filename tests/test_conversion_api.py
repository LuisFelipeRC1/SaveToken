from fastapi.testclient import TestClient

from app.api.routes import conversion as conversion_route
from app.main import app
from app.services.conversion_service import ConversionResult
from app.services.token_count_service import TokenMetrics


client = TestClient(app)


def fake_conversion_result(mode: str = "faithful") -> ConversionResult:
    metrics = TokenMetrics(
        tokenizer="cl100k_base",
        tokens_before=10,
        tokens_after=10 if mode == "faithful" else 8,
        token_difference=0 if mode == "faithful" else 2,
        reduction_percentage=0.0 if mode == "faithful" else 20.0,
    )
    return ConversionResult(
        filename="document.pdf",
        mode=mode,  # type: ignore[arg-type]
        markdown_content="# Converted",
        faithful_markdown="# Converted",
        token_metrics=metrics,
    )


def test_conversion_returns_markdown_download(monkeypatch) -> None:
    async def fake_convert(pdf, mode):
        return fake_conversion_result(mode)

    monkeypatch.setattr(conversion_route, "convert_document", fake_convert)

    response = client.post(
        "/api/v1/conversions",
        files={"pdf": ("document.pdf", b"ignored", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.text == "# Converted"
    assert response.headers["content-type"].startswith("text/markdown")
    assert "document.md" in response.headers["content-disposition"]
    assert response.headers["x-savetoken-mode"] == "faithful"


def test_optimized_mode_is_forwarded(monkeypatch) -> None:
    received = {}

    async def fake_convert(pdf, mode):
        received["mode"] = mode
        return fake_conversion_result(mode)

    monkeypatch.setattr(conversion_route, "convert_document", fake_convert)

    response = client.post(
        "/api/v1/conversions",
        data={"mode": "optimized"},
        files={"pdf": ("document.pdf", b"ignored", "application/pdf")},
    )

    assert response.status_code == 200
    assert received["mode"] == "optimized"
    assert response.headers["x-savetoken-mode"] == "optimized"


def test_invalid_mode_is_rejected() -> None:
    response = client.post(
        "/api/v1/conversions",
        data={"mode": "unknown"},
        files={"pdf": ("document.pdf", b"ignored", "application/pdf")},
    )

    assert response.status_code == 422


def test_missing_pdf_is_rejected() -> None:
    response = client.post("/api/v1/conversions", data={"mode": "faithful"})

    assert response.status_code == 422


def test_legacy_route_remains_available(monkeypatch) -> None:
    async def fake_convert(pdf, mode):
        return fake_conversion_result(mode)

    monkeypatch.setattr(conversion_route, "convert_document", fake_convert)

    response = client.post(
        "/convert",
        files={"pdf": ("document.pdf", b"ignored", "application/pdf")},
    )

    assert response.status_code == 200
