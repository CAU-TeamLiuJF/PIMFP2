from enum import IntEnum
from typing import Type, Optional, TypeVar, Generic

from peewee import IntegerField, TextField


class TinyIntField(IntegerField):
    field_type = 'TINYINT'


E = TypeVar('E', bound=IntEnum)


class TinyIntEnumField(TinyIntField, Generic[E]):
    def __init__(self, enum_clz: Type[E], *args, **kwargs):
        self.enum_clz = enum_clz
        super().__init__(*args, **kwargs)

    def db_value(self, value: Optional[E]) -> Optional[int]:
        if value is None:
            return None

        if isinstance(value, self.enum_clz):
            return int(value.value)
        raise ValueError(f'{value} is not an instance of {self.enum_clz.__name__}')

    def python_value(self, value: Optional[int]) -> Optional[E]:
        if value is None:
            return None
        try:
            return self.enum_clz(value)
        except ValueError:
            raise

class MediumTextField(TextField):
    field_type = 'MEDIUMTEXT'
