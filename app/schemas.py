from __future__ import annotations

from pydantic import BaseModel, Field


class ParseHtmlRequest(BaseModel):
    html: str = Field(
        ...,
        min_length=1,
        description="Raw Amazon-cart-like HTML pasted into the API.",
    )


class ParsedProduct(BaseModel):
    title: str
    brand: str | None
    extraction_method: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class ParseHtmlResponse(BaseModel):
    products: list[ParsedProduct]
    product_count: int = Field(ge=0)
