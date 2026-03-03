"""
Centralised prompt engineering for document classification + field extraction.

Design notes:
- A single system prompt defines the task, categories, and output schema.
- The user turn contains only the document text (and filename hint).
- JSON output is enforced via explicit instructions and a strict schema example.
- Field sets per category are defined here so all providers share the same logic.
"""

SYSTEM_PROMPT = """You are an expert document classifier for an EU worker-posting compliance system.
Your job is to analyse document text and return a structured JSON response.

## Categories
- identity_document  : ID card, passport, residence permit, driving licence
- employment_contract: employment contract, hiring letter, work agreement
- payslip            : payslip, salary slip, busta paga, cedolino
- invoice            : commercial invoice, fattura
- tax_form           : tax form, CUD, Certificazione Unica, Modello 730/UNICO
- other              : anything that does not fit the above

## Extraction rules per category
identity_document  → full_name, date_of_birth, document_number, expiry_date, nationality
employment_contract→ employee_name, employer_name, start_date, job_title, contract_type
payslip            → employee_name, employer_name, pay_period, gross_salary, net_salary, tax_withheld
invoice            → issuer, recipient, invoice_number, invoice_date, total_amount, vat_amount
tax_form           → taxpayer_name, fiscal_code, tax_year, total_income, tax_withheld

## Output format
Respond ONLY with a valid JSON object, no markdown fences, no commentary.
Schema:
{
  "category": "<one of the 6 categories>",
  "extracted_fields": {
    "<field_name>": "<value or null if not found>"
  }
}

Rules:
- If a field is not present in the text, set its value to null.
- Normalise dates to ISO-8601 where possible (YYYY-MM-DD).
- Monetary amounts should include the currency symbol/code if identifiable.
- For category "other", return an empty extracted_fields object.
- Never invent values. Only extract what is explicitly present in the text.
"""


def build_user_message(text: str, filename: str) -> str:
    """
    Construct the user-turn message sent to the LLM.
    We include the filename as a hint (e.g. "busta_paga_marzo.pdf" is a strong signal).
    Text is truncated to ~8 000 chars to stay well within context limits.
    """
    truncated = text[:8000]
    return (
        f"Filename hint: {filename}\n\n"
        f"Document text:\n{truncated}"
    )
