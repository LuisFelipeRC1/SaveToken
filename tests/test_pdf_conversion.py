import sys
import types

import pytest

from app.services.pdf_conversion_service import (
    PDFConversionError,
    convert_pdf_to_markdown,
)


def install_fake_docling(monkeypatch: pytest.MonkeyPatch, markdown: str = "# Result") -> dict[str, int]:
    calls = {"convert": 0}

    class FakeDocumentStream:
        def __init__(self, name: str, stream: object) -> None:
            self.name = name
            self.stream = stream

    class FakeDocument:
        def export_to_markdown(self) -> str:
            return markdown

    class FakeConverter:
        def __init__(self) -> None:
            pass

        def convert(self, source: FakeDocumentStream) -> object:
            assert source.name == "document.pdf"
            assert source.stream.read(5) == b"%PDF-"
            calls["convert"] += 1
            return types.SimpleNamespace(status="success", document=FakeDocument())

    docling_module = types.ModuleType("docling")
    datamodel_module = types.ModuleType("docling.datamodel")
    base_models_module = types.ModuleType("docling.datamodel.base_models")
    converter_module = types.ModuleType("docling.document_converter")
    base_models_module.DocumentStream = FakeDocumentStream
    converter_module.DocumentConverter = FakeConverter

    monkeypatch.setitem(sys.modules, "docling", docling_module)
    monkeypatch.setitem(sys.modules, "docling.datamodel", datamodel_module)
    monkeypatch.setitem(sys.modules, "docling.datamodel.base_models", base_models_module)
    monkeypatch.setitem(sys.modules, "docling.document_converter", converter_module)
    return calls


def test_pdf_is_converted_once_and_exported(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = install_fake_docling(monkeypatch)

    markdown = convert_pdf_to_markdown(b"%PDF-1.7 fake", "folder\\document.pdf")

    assert markdown == "# Result"
    assert calls["convert"] == 1


def test_empty_conversion_result_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    install_fake_docling(monkeypatch, markdown="   ")

    with pytest.raises(PDFConversionError, match="empty Markdown"):
        convert_pdf_to_markdown(b"%PDF-1.7 fake", "document.pdf")
