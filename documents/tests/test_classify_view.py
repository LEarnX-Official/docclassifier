"""
Tests for POST /api/documents/classify/
Covers: happy path (single + multiple files), invalid format,
        file too large, LLM unreachable.
"""
import uuid
from io import BytesIO
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from documents.llm.base import LLMProviderError
from documents.tests.fixtures import make_pdf_upload, make_image_upload, make_classification_result


MOCK_SETTINGS = {
    "LLM_PROVIDER": "anthropic",
    "ANTHROPIC_API_KEY": "test-key",
    "LLM_TIMEOUT_SECONDS": 10,
}


class ClassifyViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/documents/classify/"

    def _mock_pipeline(self, result=None):
        """Patch the full pipeline so no real extraction or LLM call is made."""
        if result is None:
            result = make_classification_result()
        return patch("documents.views.process_document", return_value=self._make_doc(result))

    def _make_doc(self, result):
        """Create an unsaved ClassifiedDocument-like object from a ClassificationResult."""
        from documents.models import ClassifiedDocument
        import time
        doc = ClassifiedDocument(
            filename="test.pdf",
            category=result.category,
            confidence="high",
            extracted_fields=result.extracted_fields,
            raw_text_preview="Preview text...",
            model_used=result.model_used,
            processing_time_ms=500,
        )
        doc.save()
        return doc

    # --- Happy paths ---

    def test_single_pdf_happy_path(self):
        upload = make_pdf_upload("busta_paga.pdf")
        with patch("documents.views.process_document") as mock_proc:
            mock_proc.return_value = self._make_doc(make_classification_result())
            response = self.client.post(self.url, {"files": upload}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 1)
        result = data["results"][0]
        self.assertEqual(result["category"], "payslip")
        self.assertIn("id", result)
        self.assertIn("extracted_fields", result)

    def test_multiple_files_happy_path(self):
        uploads = [
            make_pdf_upload("doc1.pdf"),
            make_pdf_upload("doc2.pdf"),
        ]
        with patch("documents.views.process_document") as mock_proc:
            mock_proc.return_value = self._make_doc(make_classification_result())
            response = self.client.post(
                self.url,
                {"files": uploads},
                format="multipart",
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.json()["results"]), 2)

    # --- Validation errors ---

    def test_no_files_returns_400(self):
        response = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_too_many_files_returns_400(self):
        uploads = [make_pdf_upload(f"doc{i}.pdf") for i in range(4)]
        response = self.client.post(self.url, {"files": uploads}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Too many files", response.json()["error"])

    def test_invalid_extension_returns_400(self):
        bad_file = SimpleUploadedFile("script.exe", b"MZ\x90\x00", content_type="application/octet-stream")
        response = self.client.post(self.url, {"files": bad_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_file_too_large_returns_400(self):
        big_content = b"%PDF-1.4 " + b"x" * (6 * 1024 * 1024)  # 6 MB
        big_file = SimpleUploadedFile("big.pdf", big_content, content_type="application/pdf")
        response = self.client.post(self.url, {"files": big_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("exceeds", response.json()["error"])

    # --- LLM errors ---

    def test_llm_unreachable_returns_503(self):
        upload = make_pdf_upload("doc.pdf")
        with patch("documents.views.process_document", side_effect=LLMProviderError("Connection refused")):
            response = self.client.post(self.url, {"files": upload}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("LLM provider unavailable", response.json()["error"])
