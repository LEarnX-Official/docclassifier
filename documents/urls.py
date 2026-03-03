from django.urls import path
from .views import ClassifyDocumentsView, DocumentDetailView, DocumentListView

urlpatterns = [
    path("classify/", ClassifyDocumentsView.as_view(), name="documents-classify"),
    path("<uuid:pk>/", DocumentDetailView.as_view(), name="documents-detail"),
    path("", DocumentListView.as_view(), name="documents-list"),
]
