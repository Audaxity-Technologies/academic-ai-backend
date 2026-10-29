from html import escape


def escape_note_text(value):
    """Treat generated/user-edited note strings as text in document markup."""
    if isinstance(value, str):
        return escape(value, quote=False)
    if isinstance(value, list):
        return [escape_note_text(item) for item in value]
    if isinstance(value, dict):
        return {key: escape_note_text(item) for key, item in value.items()}
    return value
