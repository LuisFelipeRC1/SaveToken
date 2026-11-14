from app.services.markdown_optimization_service import (
    is_safe_transformation,
    optimize_markdown,
    select_optimized_markdown,
)
from app.services.token_count_service import calculate_token_metrics


def test_optimized_markdown_normalizes_only_whitespace() -> None:
    source = "# Title\r\n\r\n\r\nParagraph   \r\n\r\n\r\n| A | B |\r\n|---|---|\r\n| 1 | 2 |"

    optimized = optimize_markdown(source)

    assert optimized == "# Title\n\nParagraph  \n\n| A | B |\n|---|---|\n| 1 | 2 |"
    assert "Paragraph" in optimized
    assert "| 1 | 2 |" in optimized


def test_token_metrics_report_zero_faithful_reduction() -> None:
    markdown = "# Title\n\nContent"

    metrics = calculate_token_metrics(markdown, markdown)

    assert metrics.tokens_before == metrics.tokens_after
    assert metrics.token_difference == 0
    assert metrics.reduction_percentage == 0
    assert metrics.tokenizer == "cl100k_base"


def test_token_metrics_handle_empty_input() -> None:
    metrics = calculate_token_metrics("", "")

    assert metrics.tokens_before == 0
    assert metrics.tokens_after == 0
    assert metrics.reduction_percentage == 0


def test_optimization_preserves_code_math_and_hard_breaks() -> None:
    source = (
        "Text   \n\n\n"
        "```python\n"
        "value  =  1  \n"
        "\n\n"
        "```\n\n"
        "$$\n"
        "x  +  y\n"
        "$$\n"
        "line break  \n"
    )

    optimized = optimize_markdown(source)

    assert "value  =  1  \n\n" in optimized
    assert "$$\nx  +  y\n$$" in optimized
    assert optimized.endswith("line break  \n")
    assert is_safe_transformation(source, optimized)


def test_optimized_candidate_must_not_remove_content() -> None:
    class FakeDocument:
        def export_to_markdown(self, **kwargs: object) -> str:
            return "# Title\n\nContent removed"

    source = "# Title\n\nContent retained"
    optimized, metrics = select_optimized_markdown(FakeDocument(), source)

    assert optimized == source
    assert metrics.tokens_after == metrics.tokens_before


def test_compact_tables_candidate_is_selected_when_cheaper(monkeypatch) -> None:
    class FakeDocument:
        def export_to_markdown(self, **kwargs: object) -> str:
            assert kwargs == {"compact_tables": True}
            return "# Title\n\n|A|B|\n|---|---|\n|1|2|"

    source = "# Title\n\n| A | B |\n| --- | --- |\n| 1 | 2 |"
    optimized, metrics = select_optimized_markdown(FakeDocument(), source)

    assert optimized == "# Title\n\n|A|B|\n|---|---|\n|1|2|"
    assert metrics.tokens_after < metrics.tokens_before
