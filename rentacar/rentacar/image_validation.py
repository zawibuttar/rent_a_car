from django.conf import settings

IMAGE_EXTENSIONS = (
    '.jpg', '.jpeg', '.jpe', '.jfif', '.png', '.gif', '.webp', '.bmp',
    '.tif', '.tiff', '.heic', '.heif', '.avif', '.svg', '.ico', '.ppm', '.pgm',
)


def _is_image_content_type(content_type):
    return (content_type or '').lower().startswith('image/')


def _has_image_extension(name):
    name = (name or '').lower()
    return any(name.endswith(ext) for ext in IMAGE_EXTENSIONS)


def validate_car_image_file(image_file):
    """Return error message string, or None if valid."""
    if not image_file:
        return 'No image file provided.'
    if image_file.size > settings.CAR_IMAGE_MAX_BYTES:
        max_mb = settings.CAR_IMAGE_MAX_BYTES / (1024 * 1024)
        return f'Image must be {max_mb:.0f} MB or smaller.'

    content_type = (getattr(image_file, 'content_type', '') or '').lower()
    name = (getattr(image_file, 'name', '') or '').lower()

    if _is_image_content_type(content_type):
        return None
    if _has_image_extension(name):
        return None

    return 'File must be an image.'
