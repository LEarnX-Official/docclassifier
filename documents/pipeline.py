"""
Document processing pipeline.
Orchestrates: extraction → LLM classification → confidence scoring → persistence.
"""
import os
import time
from dataclasses import dataclass

from django.core.files.uploadedfile import InMemoryUploadedFile

from .extractors import extract_text_from_pdf, extract_text_from_image
from .llm import get_llm_provider, LLMProviderError
from .confidence import compute_confidence
from .models import ClassifiedDocument

RAW_TEXT_PREVIEW_LEN = 300


@dataclass
class ProcessingError:
    filename: str
    error: str


def _extract_text(upload) -> str:
    """Dispatch to PDF or image extractor based on MIME / extension."""
    name_lower = upload.name.lower()
    if name_lower.endswith(".pdf"):
        return extract_text_from_pdf(upload)
    else:
        return extract_text_from_image(upload)


def process_document(upload) -> ClassifiedDocument:
    """
    Full pipeline for a single uploaded file.
    Returns a saved ClassifiedDocument instance.
    Raises LLMProviderError or any extractor exception on failure.
    """
    start_ms = time.monotonic() * 1000

    raw_text = _extract_text(upload)

    provider = get_llm_provider()
    result = provider.classify_and_extract(raw_text, upload.name)

    confidence = compute_confidence(
        category=result.category,
        extracted_fields=result.extracted_fields,
        raw_text=raw_text,
        filename=upload.name,
    )

    elapsed_ms = int(time.monotonic() * 1000 - start_ms)

    doc = ClassifiedDocument.objects.create(
        filename=upload.name,
        category=result.category,
        confidence=confidence,
        extracted_fields=result.extracted_fields,
        raw_text_preview=raw_text[:RAW_TEXT_PREVIEW_LEN],
        model_used=result.model_used,
        processing_time_ms=elapsed_ms,
    )
    return doc
