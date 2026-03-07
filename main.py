# Purpose: Starts the FastAPI application and exposes the initial API endpoints.

from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile

from brand_extractor import extract_brands_from_html
from schemas import ExtractBrandsRequest, ExtractBrandsResponse

app = FastAPI(title="Brand Extractor POC")

ALLOWED_HTML_EXTENSIONS = {".html", ".htm"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract-brands", response_model=ExtractBrandsResponse)
def extract_brands(payload: ExtractBrandsRequest) -> ExtractBrandsResponse:
    return extract_brands_from_html(html=payload.html, source=payload.source)


@app.post("/extract-brands-file", response_model=ExtractBrandsResponse)
async def extract_brands_file(file: UploadFile | None = File(default=None)) -> ExtractBrandsResponse:
    if file is None:
        raise HTTPException(status_code=400, detail="An HTML file is required.")

    filename = (file.filename or "").strip()
    if not filename:
        raise HTTPException(status_code=400, detail="The uploaded file must have a name.")

    lower_name = filename.lower()
    if not any(lower_name.endswith(extension) for extension in ALLOWED_HTML_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Only .html or .htm files are supported.")

    try:
        contents = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="The uploaded file could not be read.") from exc

    try:
        html = contents.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file must be UTF-8 text.",
        ) from exc

    return extract_brands_from_html(html=html, source="amazon_cart")
