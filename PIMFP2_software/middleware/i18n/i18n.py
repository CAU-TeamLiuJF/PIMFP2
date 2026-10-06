from pathlib import Path
from typing import Union
import json
import glom
from pimfp import logger

LOGGER = logger.get_logger(__name__)


class I18n:
    def __init__(self, localedir: Union[str, Path], locales: set[str]):
        self.localedir = Path(localedir)
        self.i18n = {}

        for domain in self.localedir.iterdir():
            if not domain.is_dir():
                continue

            translations = {}
            for locale_json in domain.glob("*.json"):
                locale = locale_json.stem
                if not locale in locales:
                    LOGGER.warning(f"{domain.name}:{locale_json.name} is ignored due to unknown locale '{locale}'")
                    continue

                translations[locale] = json.loads(locale_json.read_text(encoding="utf-8"))
            self.i18n[domain.name] = translations

    def t(self, domain: str, key: str, locale: str, *args, **kwargs):
        full_key = f"{domain}.{locale}.{key}"
        try:
            msg = glom.glom(self.i18n, full_key)
        except glom.GlomError:
            LOGGER.warning(f"{full_key} is not found")
            return None

        if msg is None:
            LOGGER.warning(f"{full_key} is None")
            return None

        if not isinstance(msg, str):
            msg = str(msg)
            LOGGER.warning(f"{full_key} is not a string, stringify it")

        if not args and not kwargs:
            return msg

        try:
            if args and kwargs:
                return msg.format(*args, **kwargs)
            elif args:
                return msg.format(*args)
            else:  # kwargs
                return msg.format(**kwargs)
        except Exception as e:
            LOGGER.error(f"{full_key} format failed", exc_info=e)
            return None
