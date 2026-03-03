"""
File validation helpers.
Validates MIME type, extension and file size against configured limits.
"""
import os
import magic
from django.conf import settings
from rest_framework.exceptions import ValidationError


MAX_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def validate_file(upload) -> None:
    """
    Raise ValidationError if the uploaded file fails any check:
      - extension not in allowed set
      - MIME type not in allowed set
      - size exceeds MAX_UPLOAD_SIZE_MB
    """
    ext = os.path.splitext(upload.name)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File '{upload.name}': extension '{ext}' is not allowed. "
            f"Allowed: {sorted(settings.ALLOWED_EXTENSIONS)}"
        )

    # Read a small header for MIME sniffing, then rewind
    header = upload.read(2048)
    upload.seek(0)
    mime = magic.from_buffer(header, mime=True)
    if mime not in settings.ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"File '{upload.name}': MIME type '{mime}' is not allowed. "
            f"Allowed: {sorted(settings.ALLOWED_MIME_TYPES)}"
        )

    upload.seek(0, 2)  # seek to end
    size = upload.tell()
    upload.seek(0)
    if size > MAX_SIZE_BYTES:
        raise ValidationError(
            f"File '{upload.name}': size {size / (1024*1024):.2f} MB exceeds "
            f"the {settings.MAX_UPLOAD_SIZE_MB} MB limit."
        )
