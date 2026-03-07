# Purpose: Starts the FastAPI application and exposes the initial API endpoints.

from __future__ import annotations

from fastapi import FastAPI

from brand_extractor import extract_brands_from_html
from schemas import ExtractBrandsRequest, ExtractBrandsResponse

app = FastAPI(title="Brand Extractor POC")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract-brands", response_model=ExtractBrandsResponse)
def extract_brands(payload: ExtractBrandsRequest) -> ExtractBrandsResponse:
    return extract_brands_from_html(html=payload.html, source=payload.source)
