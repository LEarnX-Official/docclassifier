"""
Image text extraction via EasyOCR.

Choice rationale (documented in README):
- EasyOCR supports 80+ languages out of the box (important for Italian/English docs).
- Tesseract requires a system install and per-language data packs; EasyOCR is pure Python.
- EasyOCR is more accurate on low-res scans common in HR/payroll documents.
- We load the reader once per process and reuse it to avoid repeated model loading.
"""
import io
import threading
import numpy as np
from PIL import Image

# Lazy singleton to avoid loading heavy model at import time
_reader = None
_reader_lock = threading.Lock()


def _get_reader():
    global _reader
    if _reader is None:
        with _reader_lock:
            if _reader is None:
                import easyocr
                _reader = easyocr.Reader(["en", "it"], gpu=False, verbose=False)
    return _reader


def extract_text_from_image(file_obj) -> str:
    """
    Run OCR on an image file-like object.
    Returns extracted text joined by newlines.
    """
    file_obj.seek(0)
    img = Image.open(io.BytesIO(file_obj.read())).convert("RGB")
    img_array = np.array(img)

    reader = _get_reader()
    results = reader.readtext(img_array, detail=0, paragraph=True)
    return "\n".join(results).strip()
