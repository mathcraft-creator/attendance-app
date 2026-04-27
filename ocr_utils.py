from __future__ import annotations

from io import BytesIO
from typing import List

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


def ocr_image_bytes(image_bytes: bytes, lang: str = "kor+eng") -> str:
    image = Image.open(BytesIO(image_bytes))
    return pytesseract.image_to_string(image, lang=lang)


def ocr_pdf_bytes(pdf_bytes: bytes, lang: str = "kor+eng") -> str:
    images = convert_from_bytes(pdf_bytes)
    page_texts: List[str] = []
    for i, image in enumerate(images, start=1):
        text = pytesseract.image_to_string(image, lang=lang)
        page_texts.append(f"\n\n[Page {i}]\n{text.strip()}")
    return "\n".join(page_texts).strip()
