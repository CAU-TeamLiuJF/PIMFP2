from typing import Optional

from pimfp.resources import ResourcesReader

from .i18n import I18n

i18n: Optional[I18n] = None


def init_i18n(locales: set[str]) -> I18n:
    """
    Initialize the i18n.

    Args:
        locales: locales to support.
    """
    global i18n

    i18n = I18n(ResourcesReader.resource_path("i18n"), locales)
    return i18n


__all__ = [
    "init_i18n",
    "i18n",
    "I18n"
]
