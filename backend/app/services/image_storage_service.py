import io
import logging
from typing import Tuple
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_MIME_TYPES = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}

MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # 5 MB


class ImageStorageService:
    """
    Secure In-Memory & Local Processing Service for Outfit Images.
    Validates MIME type, enforces size constraints, and verifies decodability via Pillow.
    Ensures images are kept secure in memory or cleaned up immediately, never exposed publicly.
    """

    @classmethod
    async def validate_and_read_image(
        cls,
        file: UploadFile,
    ) -> Tuple[bytes, str]:
        """
        Validates the uploaded file:
        1. MIME/content type validation
        2. File size ceiling validation (5MB max)
        3. Image byte structure and Pillow decoding verification
        Returns:
            Tuple of (raw_bytes, normalized_mime_type)
        Raises:
            HTTPException with status 400/422 if invalid, oversized, or corrupt.
        """
        if not file or not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No image file provided.",
            )

        content_type = (file.content_type or "").lower().strip()
        if content_type not in ALLOWED_IMAGE_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported image type '{content_type}'. "
                    f"Allowed formats are JPEG, PNG, and WEBP."
                ),
            )

        # Read contents
        try:
            image_bytes = await file.read()
        except Exception as e:
            logger.error(f"Failed to read uploaded image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to read uploaded image.",
            )

        # Size check
        if len(image_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image file is empty.",
            )

        if len(image_bytes) > MAX_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Image file exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
            )

        # Content verification using Pillow
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
                expected_format = ALLOWED_IMAGE_MIME_TYPES[content_type]
                # If content_type was image/jpg, normalize to image/jpeg
                normalized_mime = "image/jpeg" if content_type == "image/jpg" else content_type
                return image_bytes, normalized_mime
        except (UnidentifiedImageError, OSError, Exception) as e:
            logger.warning(f"Corrupt or counterfeit image file rejected: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupt or invalid image file content.",
            )


image_storage_service = ImageStorageService()
