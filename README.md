# Purpose: Explains how to install dependencies and run the backend-only API locally.

# Brand Extractor POC

This project is a backend-only proof of concept built with FastAPI.

It accepts pasted HTML and returns structured JSON for Amazon-cart-like items.

Current status:
- The API endpoints are wired up.
- The extractor uses simple BeautifulSoup-based parsing heuristics.
- No live scraping is implemented.
- A local fixture file is included for repeatable parser tests.
- An optional file-upload endpoint accepts local `.html` files and reuses the same parser.

## Requirements

- Python 3.10+
- A virtual environment in this project folder

## Install Dependencies

If your virtual environment is not active yet:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run The API

Start the local server:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive docs:

```text
http://127.0.0.1:8000/docs
```

## How The Extractor Works

At a high level, the extractor does four things:

1. Parses the provided HTML with BeautifulSoup using Python's built-in `html.parser`.
2. Looks for cart-item-like container nodes using a small list of Amazon-oriented selectors.
3. Extracts a title from each item using common title selectors and safe text cleanup.
4. Infers a brand by checking nearby metadata first, then falling back to the first 1-3 title tokens when they look like a brand.

Confidence is intentionally simple:
- explicit nearby brand metadata = high confidence
- title-prefix inference = medium confidence
- no strong brand signal = low confidence

## Limitations

- This is heuristic parsing, not a full Amazon DOM parser.
- HTML structure can vary a lot between carts, wishlists, orders, and experiments.
- Brand detection is only a best-effort guess based on nearby labels or title prefixes.
- Some generic titles will correctly return `null` for brand.
- Malformed HTML is handled as safely as possible, but extraction quality may drop.

## Why This Is Only A Parsing Proof Of Concept

- It does not fetch live Amazon pages over HTTP.
- It does not use browser automation.
- It only parses HTML that is pasted into the API or loaded from a local fixture file.
- It is intentionally small and explicit so the parsing behavior is easy to inspect and improve.

## Fixture File

The local fixture file lives at `fixtures/amazon_cart_sample.html`.

It exists so you can:
- run tests against a stable sample input
- exercise multiple cart items in one request
- improve the parser without needing live Amazon pages

## Test The Health Endpoint

```bash
curl http://127.0.0.1:8000/health
```

## Test The Extract Endpoint

```bash
curl -X POST http://127.0.0.1:8000/extract-brands \
  -H "Content-Type: application/json" \
  -d '{
    "html": "<html><body><div>Example cart HTML</div></body></html>",
    "source": "amazon_cart"
  }'
```

Example response shape:

```json
{
  "source": "amazon_cart",
  "item_count": 1,
  "items": [
    {
      "title": "Example cart HTML",
      "brand": null,
      "extraction_method": "title:text_fallback+no_brand_signal",
      "confidence": 0.2
    }
  ]
}
```

## Test The File Upload Endpoint

You can test the file-upload endpoint in Swagger UI:

1. Start the API with `uvicorn main:app --reload`
2. Open `http://127.0.0.1:8000/docs`
3. Expand `POST /extract-brands-file`
4. Click `Try it out`
5. Choose `fixtures/amazon_cart_sample.html`
6. Click `Execute`

You can also test it with `curl`:

```bash
curl -X POST http://127.0.0.1:8000/extract-brands-file \
  -F "file=@fixtures/amazon_cart_sample.html"
```

The file-upload endpoint:
- accepts one local `.html` or `.htm` file
- reads the file contents as text
- passes the HTML into the same extraction logic used by `/extract-brands`
- returns the same response schema

Validation behavior:
- missing file -> `400` with `An HTML file is required.`
- wrong extension -> `400` with `Only .html or .htm files are supported.`
- unreadable contents -> `400` with `The uploaded file must be UTF-8 text.`

## Run Tests

```bash
pytest
```

The main API test file is:

```text
tests/test_extract_brands.py
```
