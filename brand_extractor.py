# Purpose: Parses pasted Amazon-cart-like HTML and returns extracted item and brand information.

from __future__ import annotations

from bs4 import BeautifulSoup, Tag

from schemas import ExtractBrandsResponse, ExtractedItem

# Amazon-cart-like assumptions live here so retailer-specific choices stay in one place.
CART_ITEM_SELECTORS = (
    "[data-cart-item='true']",
    ".sc-list-item",
    ".sc-list-body .sc-list-item-content",
    ".cart-item",
)

TITLE_SELECTORS = (
    ".sc-product-title",
    "[data-product-title]",
    "a[title]",
    "h2",
    "a",
)

METADATA_SELECTORS = (
    ".a-color-secondary",
    ".a-size-small",
    ".a-size-base",
    "span",
    "div",
)

TITLE_STOP_TOKENS = {
    "for",
    "with",
    "and",
    "the",
    "a",
    "an",
    "of",
    "to",
    "from",
    "by",
}

GENERIC_FIRST_WORDS = {
    "adapter",
    "batteries",
    "battery",
    "bundle",
    "cable",
    "charger",
    "coffee",
    "cover",
    "headphones",
    "keyboard",
    "laptop",
    "mouse",
    "pack",
    "phone",
    "portable",
    "set",
    "shirt",
    "speaker",
    "tumbler",
    "wireless",
}

ALLOWED_BRAND_SUFFIXES = {
    "Basics",
    "Beauty",
    "Co",
    "Essentials",
    "Home",
    "Labs",
    "Life",
    "Plus",
    "Works",
}

HIGH_CONFIDENCE = 0.95
MEDIUM_CONFIDENCE = 0.72
LOW_CONFIDENCE = 0.2


def extract_brands_from_html(html: str, source: str) -> ExtractBrandsResponse:
    """
    Parse provided HTML only.

    This function does not fetch live pages. It only inspects HTML passed into
    the API request or loaded from a local fixture file.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    item_nodes = detect_cart_item_nodes(soup)

    items: list[ExtractedItem] = []
    for node in item_nodes:
        if not isinstance(node, Tag):
            continue

        title, title_method = extract_title_from_node(node)
        if not title:
            continue

        brand = infer_brand_from_nearby_metadata(node)
        if brand:
            items.append(
                ExtractedItem(
                    title=title,
                    brand=brand,
                    extraction_method=f"{title_method}+nearby_metadata",
                    confidence=HIGH_CONFIDENCE,
                )
            )
            continue

        brand = infer_brand_from_title(title)
        if brand:
            items.append(
                ExtractedItem(
                    title=title,
                    brand=brand,
                    extraction_method=f"{title_method}+title_prefix",
                    confidence=MEDIUM_CONFIDENCE,
                )
            )
            continue

        items.append(
            ExtractedItem(
                title=title,
                brand=None,
                extraction_method=f"{title_method}+no_brand_signal",
                confidence=LOW_CONFIDENCE,
            )
        )

    return ExtractBrandsResponse(
        source=source,
        item_count=len(items),
        items=items,
    )


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return normalize_whitespace(value).strip(" \n\t:-|")


def detect_cart_item_nodes(soup: BeautifulSoup) -> list[Tag]:
    nodes: list[Tag] = []

    for selector in CART_ITEM_SELECTORS:
        try:
            nodes.extend(tag for tag in soup.select(selector) if isinstance(tag, Tag))
        except Exception:
            continue

    if nodes:
        return deduplicate_nodes(nodes)

    fallback_nodes: list[Tag] = []
    for tag in soup.find_all(["div", "li"]):
        if not isinstance(tag, Tag):
            continue
        title, _ = extract_title_from_node(tag)
        if title:
            fallback_nodes.append(tag)

    return deduplicate_nodes(fallback_nodes)


def extract_title_from_node(node: Tag) -> tuple[str | None, str]:
    for selector in TITLE_SELECTORS:
        try:
            title_tag = node.select_one(selector)
        except Exception:
            title_tag = None

        if not isinstance(title_tag, Tag):
            continue

        raw_title = title_tag.get("title") or title_tag.get_text(" ", strip=True)
        title = clean_text(raw_title)
        if title:
            return title, f"title:{selector}"

    fallback_text = clean_text(node.get_text(" ", strip=True))
    if fallback_text:
        return fallback_text, "title:text_fallback"

    return None, "title:missing"


def infer_brand_from_nearby_metadata(node: Tag) -> str | None:
    for selector in METADATA_SELECTORS:
        try:
            metadata_nodes = node.select(selector)
        except Exception:
            metadata_nodes = []

        for metadata_node in metadata_nodes:
            if not isinstance(metadata_node, Tag):
                continue

            text = clean_text(metadata_node.get_text(" ", strip=True))
            if not text:
                continue

            lowered = text.lower()

            if lowered.startswith("brand:"):
                brand = clean_text(text.split(":", 1)[1])
                if brand:
                    return brand

            if lowered.startswith("by "):
                brand = clean_text(text[3:])
                if brand:
                    return brand

            visit_prefix = "visit the "
            store_marker = " store"
            if visit_prefix in lowered and store_marker in lowered:
                start_index = lowered.find(visit_prefix) + len(visit_prefix)
                end_index = lowered.find(store_marker, start_index)
                if end_index > start_index:
                    brand = clean_text(text[start_index:end_index])
                    if brand:
                        return brand

    return None


def infer_brand_from_title(title: str) -> str | None:
    tokens = [token.strip(",()[]") for token in clean_text(title).split()]
    tokens = [token for token in tokens if token]

    if not tokens:
        return None

    if tokens[0].lower() in GENERIC_FIRST_WORDS:
        return None

    candidate_tokens: list[str] = []
    for token in tokens[:3]:
        lowered = token.lower()
        if lowered in TITLE_STOP_TOKENS:
            break

        if not looks_like_brand_token(token):
            break

        candidate_tokens.append(token)

        if len(candidate_tokens) == 2 and token in ALLOWED_BRAND_SUFFIXES:
            break

    if not candidate_tokens:
        return None

    if len(candidate_tokens) >= 2 and candidate_tokens[1] not in ALLOWED_BRAND_SUFFIXES:
        return candidate_tokens[0]

    return " ".join(candidate_tokens)


def looks_like_brand_token(token: str) -> bool:
    cleaned = token.strip(",.:;()[]")
    if len(cleaned) < 2:
        return False

    first_char = cleaned[0]
    return first_char.isupper() or cleaned.isupper() or any(char.isdigit() for char in cleaned)


def deduplicate_nodes(nodes: list[Tag]) -> list[Tag]:
    unique_nodes: list[Tag] = []
    seen_ids: set[int] = set()

    for node in nodes:
        node_id = id(node)
        if node_id in seen_ids:
            continue
        seen_ids.add(node_id)
        unique_nodes.append(node)

    return unique_nodes
