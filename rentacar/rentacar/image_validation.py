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


def validate_hero_banner_image(image_file):
    """Return error message string, or None if valid landscape hero banner."""
    if not image_file:
        return 'Image file is required.'

    max_bytes = getattr(settings, 'HERO_BANNER_MAX_BYTES', 8 * 1024 * 1024)
    if image_file.size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        return f'Image must be {max_mb:.0f} MB or smaller.'

    content_type = (getattr(image_file, 'content_type', '') or '').lower()
    name = (getattr(image_file, 'name', '') or '').lower()
    if not (_is_image_content_type(content_type) or _has_image_extension(name)):
        return 'File must be a JPEG, PNG, or WebP image.'

    min_width = getattr(settings, 'HERO_BANNER_MIN_WIDTH', 1200)
    try:
        from PIL import Image

        image_file.seek(0)
        with Image.open(image_file) as img:
            width, height = img.size
        image_file.seek(0)
    except Exception:
        return 'Could not read image. Upload a valid JPEG, PNG, or WebP file.'

    if width <= height:
        return (
            'Hero image must be landscape orientation (width greater than height). '
            'Recommended size: 1920×1080 or 1920×1280 pixels.'
        )
    if width < min_width:
        return f'Image width must be at least {min_width}px. Recommended: 1920×1080 landscape.'

    aspect = width / height
    if aspect < 1.2 or aspect > 2.8:
        return (
            'Use a wide landscape photo (about 16:9 to 21:9). '
            'Recommended: 1920×1080 or 1920×1280 pixels.'
        )

    return None


def read_image_dimensions(image_file):
    from PIL import Image

    image_file.seek(0)
    with Image.open(image_file) as img:
        return img.size
