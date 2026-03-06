from __future__ import annotations

from collections.abc import Iterable

GENERIC_TITLE_WORDS = {
    "adapter",
    "bottle",
    "bundle",
    "cable",
    "case",
    "coffee",
    "cup",
    "headphones",
    "keyboard",
    "laptop",
    "mouse",
    "pack",
    "portable",
    "set",
    "shirt",
    "speaker",
    "tumbler",
    "wireless",
}

ALLOWED_SECOND_WORDS = {
    "Basics",
    "Essentials",
}

TITLE_STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "of",
    "the",
    "with",
}

def clean_brand_text(value: str) -> str | None:
    cleaned = " ".join(value.replace("|", " ").split()).strip(" :-")
    if not cleaned:
        return None
    return cleaned


def title_brand_candidates(title: str) -> list[str]:
    words = title.split()
    if not words:
        return []

    candidates: list[str] = []

    first = words[0].strip(",.:;()[]")
    if first and first.lower() not in TITLE_STOPWORDS and len(first) > 1:
        candidates.append(first)

    if len(words) >= 2:
        first_two = " ".join(word.strip(",.:;()[]") for word in words[:2]).strip()
        if first_two and all(part.lower() not in TITLE_STOPWORDS for part in first_two.split()):
            candidates.append(first_two)

    return candidates


def first_non_empty(values: Iterable[str | None]) -> str | None:
    for value in values:
        if value:
            return value
    return None
