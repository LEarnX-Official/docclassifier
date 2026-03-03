"""
API views for document classification endpoints.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ClassifiedDocument
from .pipeline import process_document
from .serializers import ClassifiedDocumentDetailSerializer, ClassifiedDocumentListSerializer
from .validators import validate_file
from .llm import LLMProviderError


class ClassifyDocumentsView(APIView):
    """
    POST /api/documents/classify/
    Accepts up to 3 files (PDF/JPEG/PNG), classifies and extracts fields from each.
    """

    def post(self, request: Request) -> Response:
        files = request.FILES.getlist("files")

        if not files:
            return Response(
                {"error": "No files uploaded. Use field name 'files'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(files) > settings.MAX_FILES_PER_REQUEST:
            return Response(
                {
                    "error": (
                        f"Too many files. Maximum {settings.MAX_FILES_PER_REQUEST} "
                        f"files per request."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate all files before processing any
        from rest_framework.exceptions import ValidationError as DRFValidationError
        for upload in files:
            try:
                validate_file(upload)
            except DRFValidationError as exc:
                return Response(
                    {"error": exc.detail},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        results = []
        errors = []

        for upload in files:
            try:
                doc = process_document(upload)
                results.append(ClassifiedDocumentDetailSerializer(doc).data)
            except LLMProviderError as exc:
                return Response(
                    {
                        "error": "LLM provider unavailable.",
                        "detail": str(exc),
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            except Exception as exc:
                errors.append({"filename": upload.name, "error": str(exc)})

        response_data: dict = {"results": results}
        if errors:
            response_data["errors"] = errors

        http_status = (
            status.HTTP_207_MULTI_STATUS if errors else status.HTTP_201_CREATED
        )
        return Response(response_data, status=http_status)


class DocumentDetailView(APIView):
    """
    GET /api/documents/{id}/
    Returns the full classification result for a previously processed document.
    """

    def get(self, request: Request, pk: str) -> Response:
        try:
            doc = ClassifiedDocument.objects.get(pk=pk)
        except (ClassifiedDocument.DoesNotExist, ValueError):
            return Response(
                {"error": f"Document '{pk}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ClassifiedDocumentDetailSerializer(doc).data)


class DocumentListView(APIView):
    """
    GET /api/documents/
    Returns a paginated list with optional filters: ?category=payslip&confidence=high
    """

    def get(self, request: Request) -> Response:
        qs = ClassifiedDocument.objects.all()

        category = request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)

        confidence = request.query_params.get("confidence")
        if confidence:
            qs = qs.filter(confidence=confidence)

        serializer = ClassifiedDocumentListSerializer(qs, many=True)
        return Response({"count": qs.count(), "results": serializer.data})
