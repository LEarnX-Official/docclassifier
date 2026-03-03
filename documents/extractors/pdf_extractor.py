"""
PDF text extraction using pdfplumber.

Choice rationale (documented in README):
- pdfplumber preserves layout/table structure and works well for payslips/invoices
  where column alignment matters.
- PyMuPDF is faster but has a more complex API; pdfminer is lower-level.
- pdfplumber is the pragmatic middle-ground for mixed content.
"""
import io
import pdfplumber


def extract_text_from_pdf(file_obj) -> str:
    """
    Extract all text from a PDF file-like object.
    Returns a single string with pages separated by double newlines.
    Falls back gracefully on per-page errors.
    """
    file_obj.seek(0)
    raw_bytes = file_obj.read()

    pages_text: list[str] = []
    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
        for page in pdf.pages:
            try:
                text = page.extract_text() or ""
                pages_text.append(text)
            except Exception:
                pages_text.append("")

    return "\n\n".join(pages_text).strip()
