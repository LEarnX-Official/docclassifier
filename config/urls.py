from django.urls import path, include

urlpatterns = [
    path("api/documents/", include("documents.urls")),
]
