# Purpose: Verifies the parsing proof of concept against a few small HTML examples.

from __future__ import annotations

from brand_extractor import extract_brands_from_html


def test_extracts_brand_from_explicit_brand_label() -> None:
    html = """
    <div data-cart-item="true">
        <span>Brand: Stanley</span>
        <a class="sc-product-title">Quencher H2.0 Tumbler 40 oz</a>
    </div>
    """

    response = extract_brands_from_html(html=html, source="amazon_cart")

    assert response.item_count == 1
    assert response.items[0].title == "Quencher H2.0 Tumbler 40 oz"
    assert response.items[0].brand == "Stanley"
    assert response.items[0].extraction_method.endswith("nearby_metadata")
    assert response.items[0].confidence == 0.95


def test_extracts_brand_from_title_prefix_when_metadata_is_missing() -> None:
    html = """
    <div data-cart-item="true">
        <a class="sc-product-title">Amazon Basics AA Batteries 48 Count</a>
    </div>
    """

    response = extract_brands_from_html(html=html, source="amazon_cart")

    assert response.item_count == 1
    assert response.items[0].brand == "Amazon Basics"
    assert response.items[0].extraction_method.endswith("title_prefix")
    assert response.items[0].confidence == 0.72


def test_returns_null_brand_when_no_good_signal_exists() -> None:
    html = """
    <div data-cart-item="true">
        <a class="sc-product-title">Wireless Mouse for Laptop</a>
    </div>
    """

    response = extract_brands_from_html(html=html, source="amazon_cart")

    assert response.item_count == 1
    assert response.items[0].title == "Wireless Mouse for Laptop"
    assert response.items[0].brand is None
    assert response.items[0].extraction_method.endswith("no_brand_signal")
    assert response.items[0].confidence == 0.2


def test_handles_malformed_html_without_crashing() -> None:
    html = """
    <div data-cart-item="true">
        <span>Visit the Ninja Store
        <a class="sc-product-title">Dual Brew Pro Coffee System
    """

    response = extract_brands_from_html(html=html, source="amazon_cart")

    assert response.item_count == 1
    assert response.items[0].brand == "Ninja"
