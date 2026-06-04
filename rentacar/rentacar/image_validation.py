from django.conf import settings


def validate_car_image_file(image_file):
    """Return error message string, or None if valid."""
    if not image_file:
        return 'No image file provided.'
    if image_file.size > settings.CAR_IMAGE_MAX_BYTES:
        max_mb = settings.CAR_IMAGE_MAX_BYTES / (1024 * 1024)
        return f'Image must be {max_mb:.0f} MB or smaller.'
    content_type = getattr(image_file, 'content_type', '') or ''
    if content_type and content_type not in settings.CAR_IMAGE_ALLOWED_TYPES:
        return 'Image must be JPEG, PNG, or WebP.'
    name = (getattr(image_file, 'name', '') or '').lower()
    if name and not name.endswith(('.jpg', '.jpeg', '.png', '.webp')):
        return 'Image must be JPEG, PNG, or WebP.'
    return None
