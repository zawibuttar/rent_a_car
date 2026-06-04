"""Shared helpers for API views and serializers."""


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
