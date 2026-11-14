from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ConversionMode = Literal["faithful", "optimized"]


class ConversionMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: ConversionMode
    tokenizer: str = Field(description="Tokenizer used for the token estimate.")
    tokens_before: int = Field(ge=0)
    tokens_after: int = Field(ge=0)
    token_difference: int
    reduction_percentage: float
