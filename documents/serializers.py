from rest_framework import serializers
from .models import ClassifiedDocument


class ClassifiedDocumentDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer — returned by POST /classify/ and GET /{id}/"""

    id = serializers.UUIDField(format="hex_verbose")

    class Meta:
        model = ClassifiedDocument
        fields = [
            "id",
            "filename",
            "category",
            "confidence",
            "extracted_fields",
            "raw_text_preview",
            "model_used",
            "processing_time_ms",
            "created_at",
        ]


class ClassifiedDocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list endpoints."""

    id = serializers.UUIDField(format="hex_verbose")

    class Meta:
        model = ClassifiedDocument
        fields = ["id", "filename", "category", "confidence", "created_at"]
