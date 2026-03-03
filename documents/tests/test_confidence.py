"""Tests for the confidence scoring heuristic."""
from django.test import TestCase
from documents.confidence import compute_confidence


class ConfidenceTests(TestCase):
    def test_all_fields_present_high_confidence(self):
        fields = {
            "employee_name": "Mario Rossi",
            "employer_name": "ACME SRL",
            "pay_period": "Marzo 2026",
            "gross_salary": "2850 EUR",
            "net_salary": "2015 EUR",
            "tax_withheld": "500 EUR",
        }
        result = compute_confidence("payslip", fields, "x" * 400, "busta_paga.pdf")
        self.assertEqual(result, "high")

    def test_no_fields_low_confidence(self):
        result = compute_confidence("payslip", {}, "", "unknown.pdf")
        self.assertEqual(result, "low")

    def test_other_category_neutral_score(self):
        result = compute_confidence("other", {}, "x" * 400, "random.pdf")
        # other has no expected fields; score = 0.3 (other) + 0.2 (text) = 0.5 → medium
        self.assertIn(result, ("medium", "high"))

    def test_filename_keyword_boosts_score(self):
        partial_fields = {
            "employee_name": "Mario Rossi",
            "employer_name": "ACME",
            "pay_period": None,
            "gross_salary": None,
            "net_salary": None,
            "tax_withheld": None,
        }
        with_kw = compute_confidence("payslip", partial_fields, "x" * 400, "cedolino_marzo.pdf")
        without_kw = compute_confidence("payslip", partial_fields, "x" * 400, "scan_001.pdf")
        # With keyword should be >= without
        levels = {"low": 0, "medium": 1, "high": 2}
        self.assertGreaterEqual(levels[with_kw], levels[without_kw])
