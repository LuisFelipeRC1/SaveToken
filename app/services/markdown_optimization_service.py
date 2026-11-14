import logging
from dataclasses import dataclass

from app.services.token_count_service import (
    DEFAULT_TOKENIZER_ENCODING,
    TokenMetrics,
    calculate_token_metrics,
    count_tokens,
)


logger = logging.getLogger(__name__)
MAX_CONSECUTIVE_NEWLINES = 2


@dataclass(frozen=True)
class MarkdownCandidate:
    name: str
    markdown: str


def optimize_markdown(markdown: str) -> str:
    """Normalize whitespace outside protected Markdown regions."""

    if not markdown:
        return markdown

    normalized = markdown.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    output: list[str] = []
    in_fence = False
    fence_marker = ""
    in_math = False
    in_html = False
    blank_lines = 0

    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            output.append(line)
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            blank_lines = 0
            continue

        protected = in_fence or in_math or in_html
        if stripped.startswith("$$") or stripped.startswith("\\["):
            in_math = not in_math
            protected = True
        if stripped.startswith("<") and not stripped.startswith("</"):
            in_html = True
            protected = True
        if in_html and stripped == "":
            in_html = False

        if protected:
            output.append(line)
            blank_lines = 0
            continue

        if line.startswith(("    ", "\t")):
            output.append(line)
            blank_lines = 0
            continue

        if line == "":
            blank_lines += 1
            if blank_lines <= MAX_CONSECUTIVE_NEWLINES - 1:
                output.append(line)
            continue

        blank_lines = 0
        trailing_spaces = len(line) - len(line.rstrip(" "))
        if trailing_spaces >= 2:
            output.append(line.rstrip(" ") + "  ")
        else:
            output.append(line.rstrip(" "))

    return "\n".join(output)


def _content_fingerprint(markdown: str) -> str:
    """Compare every non-whitespace character, including Markdown markers."""

    return "".join(character for character in markdown if not character.isspace())


def is_safe_transformation(original: str, candidate: str) -> bool:
    return _content_fingerprint(original) == _content_fingerprint(candidate)


def generate_candidates(document: object, faithful_markdown: str) -> list[MarkdownCandidate]:
    candidates = [MarkdownCandidate("faithful", faithful_markdown)]

    try:
        compact_markdown = document.export_to_markdown(compact_tables=True)
    except Exception as exc:
        logger.warning("Docling compact Markdown export was unavailable: %s", exc)
    else:
        if (
            isinstance(compact_markdown, str)
            and compact_markdown != faithful_markdown
            and is_safe_transformation(faithful_markdown, compact_markdown)
        ):
            candidates.append(MarkdownCandidate("compact_tables", compact_markdown))

    normalized = optimize_markdown(candidates[-1].markdown)
    if (
        normalized != candidates[-1].markdown
        and is_safe_transformation(faithful_markdown, normalized)
    ):
        candidates.append(MarkdownCandidate("structural_normalization", normalized))

    return candidates


def select_optimized_markdown(
    document: object,
    faithful_markdown: str,
    encoding_name: str = DEFAULT_TOKENIZER_ENCODING,
) -> tuple[str, TokenMetrics]:
    """Select the cheapest safe candidate, never exceeding faithful token cost."""

    faithful_tokens = count_tokens(faithful_markdown, encoding_name)
    selected = faithful_markdown
    selected_tokens = faithful_tokens

    for candidate in generate_candidates(document, faithful_markdown):
        candidate_tokens = count_tokens(candidate.markdown, encoding_name)
        if candidate_tokens < selected_tokens:
            selected = candidate.markdown
            selected_tokens = candidate_tokens

    metrics = calculate_token_metrics(
        faithful_markdown,
        selected,
        encoding_name,
    )
    return selected, metrics
