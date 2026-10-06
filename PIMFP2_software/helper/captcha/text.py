import random
import string
from dataclasses import dataclass
from enum import Flag, auto
from typing import Optional


class TextCaptchaCharType(Flag):
    NONE = 0
    DIGIT = auto()
    LOWERCASE = auto()
    UPPERCASE = auto()

    LETTER = UPPERCASE | LOWERCASE
    ALPHABET = LETTER | DIGIT


@dataclass
class TextCaptchaConfig:
    length: int = 6
    char_type: TextCaptchaCharType = TextCaptchaCharType.DIGIT
    custom_chars: Optional[list[str]] = None
    exclude_chars: Optional[list[str]] = None


class TextCaptchaGeneratorBuilder:
    def __init__(self):
        self._config = TextCaptchaConfig()

    def length(self, length: int) -> 'TextCaptchaGeneratorBuilder':
        self._config.length = length
        return self

    def add_digit(self) -> 'TextCaptchaGeneratorBuilder':
        self.add_char_type(TextCaptchaCharType.DIGIT)
        return self

    def add_lowercase(self) -> 'TextCaptchaGeneratorBuilder':
        self.add_char_type(TextCaptchaCharType.LOWERCASE)
        return self

    def add_uppercase(self) -> 'TextCaptchaGeneratorBuilder':
        self.add_char_type(TextCaptchaCharType.UPPERCASE)
        return self

    def add_custom_chars(self, custom_chars: list[str]) -> 'TextCaptchaGeneratorBuilder':
        self._config.custom_chars = custom_chars
        return self

    def exclude_chars(self, exclude_chars: list[str]) -> 'TextCaptchaGeneratorBuilder':
        self._config.exclude_chars = exclude_chars
        return self

    def with_char_type(self, char_type: TextCaptchaCharType) -> 'TextCaptchaGeneratorBuilder':
        self._config.char_type = char_type
        self._config.custom_chars = None
        self._config.exclude_chars = None
        return self

    def add_char_type(self, char_type: TextCaptchaCharType) -> 'TextCaptchaGeneratorBuilder':
        self._config.char_type |= char_type
        return self

    def build(self) -> 'TextCaptchaGenerator':
        return TextCaptchaGenerator(self._config)


class TextCaptchaGenerator:
    def __init__(self, config: TextCaptchaConfig):
        self._config = config
        self._char_set = ''.join(self._build_char_set())

    def _build_char_set(self):
        char_set = set()
        if self._config.char_type & TextCaptchaCharType.DIGIT:
            char_set |= set(string.digits)
        if self._config.char_type & TextCaptchaCharType.LOWERCASE:
            char_set |= set(string.ascii_lowercase)
        if self._config.char_type & TextCaptchaCharType.UPPERCASE:
            char_set |= set(string.ascii_uppercase)
        if self._config.custom_chars:
            char_set |= set(''.join(self._config.custom_chars))
        if self._config.exclude_chars:
            char_set -= set(''.join(self._config.exclude_chars))
        return char_set

    def generate(self):
        return ''.join(random.choices(self._char_set, k=self._config.length))
