from django.conf import settings

from .image_validation import IMAGE_EXTENSIONS, _has_image_extension, _is_image_content_type

DOCUMENT_EXTENSIONS = ('.pdf', '.doc', '.docx', '.txt')

ALLOWED_ATTACHMENT_EXTENSIONS = IMAGE_EXTENSIONS + DOCUMENT_EXTENSIONS

DOCUMENT_CONTENT_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
}


def _has_document_extension(name):
    name = (name or '').lower()
    return any(name.endswith(ext) for ext in DOCUMENT_EXTENSIONS)


def _is_document_content_type(content_type):
    return (content_type or '').lower() in DOCUMENT_CONTENT_TYPES


def attachment_is_image(file_obj):
    content_type = (getattr(file_obj, 'content_type', '') or '').lower()
    name = (getattr(file_obj, 'name', '') or '').lower()
    return _is_image_content_type(content_type) or _has_image_extension(name)


def validate_message_attachment_file(file_obj):
    """Return error message string, or None if valid."""
    if not file_obj:
        return 'No file provided.'

    max_bytes = getattr(settings, 'MESSAGE_ATTACHMENT_MAX_BYTES', 10 * 1024 * 1024)
    if file_obj.size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        return f'File must be {max_mb:.0f} MB or smaller.'

    content_type = (getattr(file_obj, 'content_type', '') or '').lower()
    name = (getattr(file_obj, 'name', '') or '').lower()

    if _is_image_content_type(content_type) or _has_image_extension(name):
        return None
    if _is_document_content_type(content_type) or _has_document_extension(name):
        return None

    return 'File type not allowed. Send an image or PDF/Word/text document.'
