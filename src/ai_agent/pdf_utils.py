from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF
from PIL import Image


@dataclass(frozen=True)
class PageImage:
    page_number: int
    image_bytes: bytes
    mime_type: str = "image/png"


def iter_page_images(pdf_path: str | Path, max_pages: int, max_px: int) -> Iterable[PageImage]:
    doc = fitz.open(str(pdf_path))
    try:
        for i, page in enumerate(doc):
            if i >= max_pages:
                break
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = _resize_keep_aspect(img, max_px)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            yield PageImage(page_number=i + 1, image_bytes=buf.getvalue())
    finally:
        doc.close()


def _resize_keep_aspect(img: Image.Image, max_px: int) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_px:
        return img
    ratio = max_px / max(w, h)
    return img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

