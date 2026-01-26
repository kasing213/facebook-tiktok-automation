"""
Product Image Service - Handles product image uploads via MongoDB GridFS.
Reuses existing GridFSStorageService for storage operations.
"""
import logging
from typing import Optional, Tuple
from uuid import UUID

from app.services.ads_alert_service import GridFSStorageService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Product image constraints
MAX_IMAGE_SIZE_MB = 50
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024

ALLOWED_IMAGE_TYPES = [
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif"
]


class ProductImageService:
    """Handle product image uploads to MongoDB GridFS"""

    def __init__(self):
        self._storage = GridFSStorageService()

    def validate_image(self, content: bytes, content_type: str) -> Optional[str]:
        """
        Validate image file.

        Args:
            content: Image file content as bytes
            content_type: MIME type of the file

        Returns:
            Error message if invalid, None if valid.
        """
        # Check content type
        if content_type not in ALLOWED_IMAGE_TYPES:
            allowed = ", ".join(ALLOWED_IMAGE_TYPES)
            return f"File type '{content_type}' not allowed. Allowed types: {allowed}"

        # Check file size
        if len(content) > MAX_IMAGE_SIZE_BYTES:
            return f"Image size exceeds {MAX_IMAGE_SIZE_MB}MB limit"

        return None

    async def upload_image(
        self,
        tenant_id: UUID,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Tuple[str, str]:
        """
        Upload product image to GridFS.

        Args:
            tenant_id: Tenant ID for isolation
            file_content: Image file content as bytes
            filename: Original filename
            content_type: MIME type

        Returns:
            Tuple of (image_id, image_url)
        """
        # Add product-specific prefix to filename for organization
        prefixed_filename = f"product_{filename}"

        image_id, _ = await self._storage.upload_file(
            tenant_id=tenant_id,
            file_content=file_content,
            filename=prefixed_filename,
            content_type=content_type
        )

        # Return URL pointing to inventory image endpoint
        image_url = self.get_image_url(image_id)

        logger.info(f"Uploaded product image: {image_id} for tenant {tenant_id}")
        return image_id, image_url

    async def delete_image(self, image_id: str) -> bool:
        """
        Delete product image from GridFS.

        Args:
            image_id: GridFS file ID

        Returns:
            True if deleted successfully, False otherwise
        """
        result = await self._storage.delete_file(image_id)
        if result:
            logger.info(f"Deleted product image: {image_id}")
        return result

    async def get_image(
        self,
        image_id: str,
        tenant_id: Optional[UUID] = None
    ) -> Optional[Tuple[bytes, str, str]]:
        """
        Get image from GridFS with optional tenant validation.

        Args:
            image_id: GridFS file ID
            tenant_id: Optional tenant ID for validation

        Returns:
            Tuple of (content, content_type, filename) or None if not found
        """
        return await self._storage.get_file(image_id, tenant_id)

    def get_image_url(self, image_id: str) -> str:
        """
        Get absolute URL for product image.

        Args:
            image_id: GridFS file ID

        Returns:
            Full URL to access the image (includes backend host)
        """
        settings = get_settings()
        base_url = str(settings.BASE_URL).rstrip('/')
        return f"{base_url}/inventory/products/image/{image_id}"
