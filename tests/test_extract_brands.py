# Purpose: Exercises the API against a realistic local fixture and a few key edge cases.

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from main import app

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "amazon_cart_sample.html"

client = TestClient(app)


def test_health_returns_success() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_extract_brands_returns_expected_item_count_from_fixture() -> None:
    html = FIXTURE_PATH.read_text()

    response = client.post(
        "/extract-brands",
        json={"html": html, "source": "amazon_cart"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["source"] == "amazon_cart"
    assert body["item_count"] == 5
    assert len(body["items"]) == 5


def test_extract_brands_includes_at_least_one_high_confidence_item() -> None:
    html = FIXTURE_PATH.read_text()

    response = client.post(
        "/extract-brands",
        json={"html": html, "source": "amazon_cart"},
    )

    items = response.json()["items"]

    assert any(item["confidence"] >= 0.95 for item in items)


def test_malformed_html_does_not_crash_the_api() -> None:
    malformed_html = """
    <div data-cart-item="true">
        <span>Visit the Ninja Store
        <a class="sc-product-title">Dual Brew Pro Coffee System
    """

    response = client.post(
        "/extract-brands",
        json={"html": malformed_html, "source": "amazon_cart"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["item_count"] == 1
    assert body["items"][0]["title"] == "Dual Brew Pro Coffee System"


def test_empty_html_returns_empty_items_list() -> None:
    response = client.post(
        "/extract-brands",
        json={"html": "", "source": "amazon_cart"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "source": "amazon_cart",
        "item_count": 0,
        "items": [],
    }
