"""Shared helpers for API views and serializers."""
import re


def format_display_name(name):
    """Capitalize username for display (e.g. ahmad -> Ahmad, ahmed_ali -> Ahmed Ali)."""
    if not name:
        return ''
    s = str(name).strip()
    if not s:
        return ''
    words = re.split(r'[\s_\-]+', s)
    return ' '.join(w[:1].upper() + w[1:].lower() if w else '' for w in words if w)


def parse_bool(value):
    """Coerce request body values to bool (handles JSON strings like \"false\")."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'on')
    return bool(value)
