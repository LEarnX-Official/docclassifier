import uuid
from django.db import models


class DocumentCategory(models.TextChoices):
    IDENTITY_DOCUMENT = "identity_document", "Identity Document"
    EMPLOYMENT_CONTRACT = "employment_contract", "Employment Contract"
    PAYSLIP = "payslip", "Payslip"
    INVOICE = "invoice", "Invoice"
    TAX_FORM = "tax_form", "Tax Form"
    OTHER = "other", "Other"


class ConfidenceLevel(models.TextChoices):
    HIGH = "high", "High"
    MEDIUM = "medium", "Medium"
    LOW = "low", "Low"


class ClassifiedDocument(models.Model):
    """
    Stores the result of an LLM-based document classification.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=DocumentCategory.choices)
    confidence = models.CharField(max_length=10, choices=ConfidenceLevel.choices)
    extracted_fields = models.JSONField(default=dict)
    raw_text_preview = models.TextField(blank=True)
    model_used = models.CharField(max_length=100)
    processing_time_ms = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["confidence"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.filename} → {self.category} ({self.confidence})"
