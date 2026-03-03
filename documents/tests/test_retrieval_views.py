"""
Tests for GET /api/documents/{id}/ and GET /api/documents/?filters
"""
import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from documents.models import ClassifiedDocument


def make_doc(**kwargs):
    defaults = dict(
        filename="test.pdf",
        category="payslip",
        confidence="high",
        extracted_fields={"employee_name": "Mario Rossi"},
        raw_text_preview="Some text",
        model_used="claude-sonnet-4-20250514",
        processing_time_ms=300,
    )
    defaults.update(kwargs)
    return ClassifiedDocument.objects.create(**defaults)


class DocumentDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_existing_document_returns_200(self):
        doc = make_doc()
        response = self.client.get(f"/api/documents/{doc.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["category"], "payslip")
        self.assertEqual(data["confidence"], "high")
        self.assertIn("extracted_fields", data)

    def test_nonexistent_id_returns_404(self):
        fake_id = str(uuid.uuid4())
        response = self.client.get(f"/api/documents/{fake_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DocumentListViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        make_doc(category="payslip", confidence="high")
        make_doc(category="payslip", confidence="low")
        make_doc(category="invoice", confidence="high")

    def test_list_all_documents(self):
        response = self.client.get("/api/documents/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 3)
        self.assertEqual(len(data["results"]), 3)

    def test_filter_by_category(self):
        response = self.client.get("/api/documents/?category=payslip")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 2)
        for item in data["results"]:
            self.assertEqual(item["category"], "payslip")

    def test_filter_by_confidence(self):
        response = self.client.get("/api/documents/?confidence=high")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 2)
        for item in data["results"]:
            self.assertEqual(item["confidence"], "high")

    def test_filter_by_category_and_confidence(self):
        response = self.client.get("/api/documents/?category=payslip&confidence=high")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data["count"], 1)
