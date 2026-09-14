from PIL import Image, UnidentifiedImageError
from django.core.exceptions import ValidationError


MAX_EVIDENCE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


def validate_evidence_image(uploaded_file):
    """
    Validate an uploaded complaint evidence image.

    Validation checks:
    - File exists
    - File size is within the 5 MB limit
    - MIME type is supported
    - File contents are actually a valid image
    - Detected image format matches the allowed formats
    """
    if not uploaded_file:
        raise ValidationError("An evidence image is required.")

    if uploaded_file.size > MAX_EVIDENCE_SIZE:
        raise ValidationError(
            "Evidence image must be 5 MB or smaller."
        )

    content_type = getattr(
        uploaded_file,
        "content_type",
        "",
    ).lower()

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(
            "Unsupported image type. "
            "Only JPEG, PNG, and WEBP images are allowed."
        )

    try:
        uploaded_file.seek(0)

        with Image.open(uploaded_file) as image:
            detected_format = image.format

            if detected_format not in ALLOWED_CONTENT_TYPES.values():
                raise ValidationError(
                    "The uploaded file is not a supported image format."
                )

            image.verify()

        uploaded_file.seek(0)

    except (
        UnidentifiedImageError,
        OSError,
    ) as exc:
        raise ValidationError(
            "The uploaded file is not a valid image."
        ) from exc

    finally:
        try:
            uploaded_file.seek(0)
        except (AttributeError, OSError):
            pass

    return True