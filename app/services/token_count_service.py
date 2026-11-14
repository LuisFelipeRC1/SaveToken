from dataclasses import dataclass


DEFAULT_TOKENIZER_ENCODING = "cl100k_base"


@dataclass(frozen=True)
class TokenMetrics:
    tokenizer: str
    tokens_before: int
    tokens_after: int
    token_difference: int
    reduction_percentage: float


def count_tokens(
    text: str,
    encoding_name: str = DEFAULT_TOKENIZER_ENCODING,
) -> int:
    """Count tokens using an explicitly named tiktoken encoding."""

    import tiktoken

    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def calculate_token_metrics(
    markdown_before: str,
    markdown_after: str,
    encoding_name: str = DEFAULT_TOKENIZER_ENCODING,
) -> TokenMetrics:
    """Calculate token counts and conservative reduction metrics."""

    tokens_before = count_tokens(markdown_before, encoding_name)
    tokens_after = count_tokens(markdown_after, encoding_name)
    token_difference = tokens_before - tokens_after

    if tokens_before == 0:
        reduction_percentage = 0.0
    else:
        reduction_percentage = (token_difference / tokens_before) * 100

    return TokenMetrics(
        tokenizer=encoding_name,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        token_difference=token_difference,
        reduction_percentage=reduction_percentage,
    )
