"""Internationalization module for the expense analyzer app."""

import os
from typing import Any


def get_language() -> str:
    """Get the current language from environment variable."""
    return os.environ.get("APP_LANGUAGE", "en").lower()


def load_translations() -> dict[str, Any]:
    """Load translations for the current language."""
    lang = get_language()

    if lang == "fr":
        from translations.fr import TRANSLATIONS
    else:
        from translations.en import TRANSLATIONS

    return TRANSLATIONS


_translations: dict[str, Any] | None = None


def get_translations() -> dict[str, Any]:
    """Get cached translations."""
    global _translations
    if _translations is None:
        _translations = load_translations()
    return _translations


def t(key: str, **kwargs) -> str:
    """
    Get translation for a key.

    Args:
        key: Dot-separated key path (e.g., "app.title" or "overview.filters")
        **kwargs: Variables to format into the string

    Returns:
        Translated string with variables substituted
    """
    translations = get_translations()

    # Navigate nested dictionary using dot notation
    keys = key.split(".")
    value = translations
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Return the key itself if translation not found
            return key

    if isinstance(value, str) and kwargs:
        return value.format(**kwargs)

    return value if isinstance(value, str) else key


def get_month_names() -> dict[int, str]:
    """Get month names in current language."""
    return get_translations().get("months", {})
