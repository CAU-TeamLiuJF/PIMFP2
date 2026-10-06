from peewee import BigAutoField, CharField, DateTimeField, SQL

from . import BaseModel


class AppRole(BaseModel):
    id = BigAutoField(primary_key=True, constraints=[SQL("UNSIGNED")])
    code = CharField(64, unique=True, null=False)
    description = CharField(255, null=True)
    created_at = DateTimeField(null=False, constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(null=False, constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])

    class Meta:
        table_name = 'app_role'
