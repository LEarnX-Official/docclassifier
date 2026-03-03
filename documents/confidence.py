"""
Confidence scoring heuristic.

Algorithm (documented in README):
1. Field completeness ratio  – what fraction of expected fields were actually extracted
   (non-null values).  Weight: 60 %
2. Text length signal – very short extracted text (<100 chars) reduces confidence.
   Weight: 20 %
3. Category–filename consistency – if the filename contains a keyword strongly
   associated with the predicted category, this is a corroborating signal.
   Weight: 20 %

Scoring thresholds:
  ≥ 0.70  → high
  ≥ 0.40  → medium
  <  0.40  → low
"""

EXPECTED_FIELDS: dict[str, list[str]] = {
    "identity_document": [
        "full_name", "date_of_birth", "document_number", "expiry_date", "nationality"
    ],
    "employment_contract": [
        "employee_name", "employer_name", "start_date", "job_title", "contract_type"
    ],
    "payslip": [
        "employee_name", "employer_name", "pay_period", "gross_salary", "net_salary", "tax_withheld"
    ],
    "invoice": [
        "issuer", "recipient", "invoice_number", "invoice_date", "total_amount", "vat_amount"
    ],
    "tax_form": [
        "taxpayer_name", "fiscal_code", "tax_year", "total_income", "tax_withheld"
    ],
    "other": [],
}

_FILENAME_KEYWORDS: dict[str, list[str]] = {
    "identity_document": ["passport", "id", "identity", "carta", "passaporto", "permesso"],
    "employment_contract": ["contract", "contratto", "hiring", "assunzione"],
    "payslip": ["payslip", "busta", "cedolino", "paga", "salary"],
    "invoice": ["invoice", "fattura"],
    "tax_form": ["cud", "730", "unico", "certificazione", "tax"],
}


def compute_confidence(
    category: str,
    extracted_fields: dict,
    raw_text: str,
    filename: str,
) -> str:
    """Return 'high', 'medium', or 'low'."""
    score = 0.0

    # 1. Field completeness (60%)
    expected = EXPECTED_FIELDS.get(category, [])
    if expected:
        filled = sum(
            1 for k in expected if extracted_fields.get(k) not in (None, "", "null")
        )
        score += 0.6 * (filled / len(expected))
    else:
        # "other" has no expected fields — treat as neutral
        score += 0.3

    # 2. Text length signal (20%)
    text_len = len(raw_text.strip())
    if text_len >= 300:
        score += 0.20
    elif text_len >= 100:
        score += 0.10
    # < 100 chars → 0 points

    # 3. Filename consistency (20%)
    lower_filename = filename.lower()
    keywords = _FILENAME_KEYWORDS.get(category, [])
    if any(kw in lower_filename for kw in keywords):
        score += 0.20

    # Map score to level
    if score >= 0.70:
        return "high"
    elif score >= 0.40:
        return "medium"
    else:
        return "low"
