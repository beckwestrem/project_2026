from __future__ import annotations

from pathlib import Path

import pytest

from app.parser import parse_cart_html
from app.schemas import ParseHtmlRequest

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "amazon_cart_sample.html"


def test_parse_cart_html_from_fixture() -> None:
    html = FIXTURE_PATH.read_text()

    result = parse_cart_html(html)

    assert result.product_count == 2
    assert result.products[0].title == "Amazon Basics AA Batteries, 48 Count"
    assert result.products[0].brand == "Amazon Basics"
    assert result.products[1].brand == "Stanley"


def test_parse_returns_null_brand_when_no_signal_exists() -> None:
    html = """
    <div data-cart-item="true">
        <a class="sc-product-title">Wireless Mouse for Laptop</a>
    </div>
    """

    result = parse_cart_html(html)

    assert result.product_count == 1
    assert result.products[0].title == "Wireless Mouse for Laptop"
    assert result.products[0].brand is None
    assert result.products[0].extraction_method.endswith("brand:none")


def test_request_model_rejects_empty_html() -> None:
    with pytest.raises(Exception):
        ParseHtmlRequest(html="")


def test_parse_extracts_brand_from_store_text() -> None:
    html = """
    <div data-cart-item="true">
        <span>Visit the Ninja Store</span>
        <a class="sc-product-title">Dual Brew Pro Coffee System</a>
    </div>
    """

    result = parse_cart_html(html)

    assert result.product_count == 1
    assert result.products[0].brand == "Ninja"
    assert result.products[0].extraction_method == "title:.sc-product-title+brand:nearby_text"
    assert result.products[0].confidence_score == 0.9
