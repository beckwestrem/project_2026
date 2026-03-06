from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

from app.brand_rules import ALLOWED_SECOND_WORDS, GENERIC_TITLE_WORDS, clean_brand_text, first_non_empty, title_brand_candidates
from app.schemas import ParseHtmlResponse, ParsedProduct

TITLE_SELECTORS = (
    ".sc-product-title",
    "[data-product-title]",
    "h2",
    "a",
)

CART_ITEM_SELECTORS = (
    "[data-cart-item='true']",
    ".sc-list-item",
    ".cart-item",
)


def parse_cart_html(html: str) -> ParseHtmlResponse:
    soup = BeautifulSoup(html, "html.parser")
    item_nodes = find_cart_item_nodes(soup)

    products: list[ParsedProduct] = []
    for node in item_nodes:
        product = parse_product_node(node)
        if product is not None:
            products.append(product)

    return ParseHtmlResponse(products=products, product_count=len(products))


def find_cart_item_nodes(soup: BeautifulSoup) -> list[Tag]:
    nodes: list[Tag] = []
    for selector in CART_ITEM_SELECTORS:
        nodes.extend(tag for tag in soup.select(selector) if isinstance(tag, Tag))

    if nodes:
        return dedupe_tags(nodes)

    fallback_nodes = []
    for tag in soup.find_all(["div", "li"]):
        if isinstance(tag, Tag) and extract_title_from_node(tag):
            fallback_nodes.append(tag)

    return dedupe_tags(fallback_nodes)


def parse_product_node(node: Tag) -> ParsedProduct | None:
    title, title_method = extract_title_from_node(node)
    if not title:
        return None

    brand, brand_method, brand_confidence = infer_brand(node, title)
    extraction_parts = [title_method, brand_method]

    confidence_score = min(0.99, round((0.55 + brand_confidence), 2))
    return ParsedProduct(
        title=title,
        brand=brand,
        extraction_method="+".join(extraction_parts),
        confidence_score=confidence_score,
    )


def extract_title_from_node(node: Tag) -> tuple[str | None, str]:
    for selector in TITLE_SELECTORS:
        found = node.select_one(selector)
        if isinstance(found, Tag):
            text = normalize_text(found.get_text(" ", strip=True))
            if text:
                return text, f"title:{selector}"

    text = normalize_text(node.get_text(" ", strip=True))
    if text:
        return text, "title:text_fallback"

    return None, "title:missing"


def infer_brand(node: Tag, title: str) -> tuple[str | None, str, float]:
    text_snippets = [normalize_text(text) for text in node.stripped_strings]

    label_brand = first_non_empty(
        [extract_brand_from_label(text, "Brand:") for text in text_snippets]
        + [extract_brand_from_store_text(text) for text in text_snippets]
    )
    if label_brand:
        return label_brand, "brand:nearby_text", 0.35

    title_brand = infer_brand_from_title(title)
    if title_brand:
        return title_brand, "brand:title_prefix", 0.28

    return None, "brand:none", 0.05


def infer_brand_from_title(title: str) -> str | None:
    candidates = title_brand_candidates(title)
    if not candidates:
        return None

    if len(candidates) > 1 and looks_like_two_word_brand(candidates[1]):
        return candidates[1]

    if candidates[0].lower() in GENERIC_TITLE_WORDS:
        return None

    return candidates[0]


def extract_brand_from_label(text: str, label: str) -> str | None:
    pattern = re.compile(rf"{re.escape(label)}\s*([A-Za-z0-9][A-Za-z0-9 &'\-]+)", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    return clean_brand_text(match.group(1))


def extract_brand_from_store_text(text: str) -> str | None:
    pattern = re.compile(r"Visit the\s+(.+?)\s+Store", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return None
    return clean_brand_text(match.group(1))


def looks_like_two_word_brand(value: str) -> bool:
    words = value.split()
    if len(words) != 2:
        return False
    return words[1] in ALLOWED_SECOND_WORDS and all(word and word[0].isalnum() for word in words)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def dedupe_tags(tags: list[Tag]) -> list[Tag]:
    seen: set[int] = set()
    deduped: list[Tag] = []
    for tag in tags:
        marker = id(tag)
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(tag)
    return deduped
