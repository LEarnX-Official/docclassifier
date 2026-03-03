"""Shared test fixtures and helpers."""
import io
import uuid
from unittest.mock import MagicMock
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.llm.base import ClassificationResult


def make_pdf_upload(name="test.pdf", content=b"%PDF-1.4 test content"):
    return SimpleUploadedFile(name, content, content_type="application/pdf")


def make_image_upload(name="test.jpg", content=None):
    if content is None:
        content = (
            b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
            b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
            b"\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
            b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xff\xd9"
        )
    return SimpleUploadedFile(name, content, content_type="image/jpeg")


def make_classification_result(**kwargs):
    defaults = dict(
        category="payslip",
        extracted_fields={
            "employee_name": "Mario Rossi",
            "employer_name": "Arletti Partners SRL",
            "pay_period": "Marzo 2026",
            "gross_salary": "2850.00 EUR",
            "net_salary": "2015.00 EUR",
            "tax_withheld": "500.00 EUR",
        },
        model_used="claude-sonnet-4-20250514",
    )
    defaults.update(kwargs)
    return ClassificationResult(**defaults)
