from peewee import BigAutoField, CharField, DateTimeField, SQL

from pimfp.entity import UserStatus
from . import BaseModel
from .field import TinyIntEnumField


class AppUser(BaseModel):
    id = BigAutoField(primary_key=True, constraints=[SQL("UNSIGNED")])
    email = CharField(255, unique=True, null=False)
    organization = CharField(255, null=False)
    password = CharField(128, null=False)
    status = TinyIntEnumField(enum_clz=UserStatus, constraints=[SQL("DEFAULT 1")], null=False)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])

    class Meta:
        table_name = 'app_user'
