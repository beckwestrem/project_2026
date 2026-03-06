from __future__ import annotations

from fastapi import FastAPI

from app.parser import parse_cart_html
from app.schemas import ParseHtmlRequest, ParseHtmlResponse

app = FastAPI(title="Cart HTML Parser POC")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/parse-cart-html", response_model=ParseHtmlResponse)
def parse_cart_html_endpoint(payload: ParseHtmlRequest) -> ParseHtmlResponse:
    return parse_cart_html(payload.html)
