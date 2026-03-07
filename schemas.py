# Purpose: Defines the request and response models used by the API.

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ExtractBrandsRequest(BaseModel):
    html: str = Field(..., min_length=1, description="Raw HTML pasted into the API.")
    source: Literal["amazon_cart"] = Field(
        ...,
        description="Identifies the HTML format the parser should expect.",
    )


class ExtractedItem(BaseModel):
    title: str
    brand: str | None
    extraction_method: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class ExtractBrandsResponse(BaseModel):
    source: Literal["amazon_cart"]
    item_count: int = Field(..., ge=0)
    items: list[ExtractedItem]
