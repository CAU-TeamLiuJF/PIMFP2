from peewee import DateTimeField, BigIntegerField, SQL, CompositeKey, CharField, BigAutoField

from . import BaseModel


class AppUserRole(BaseModel):
    id = BigAutoField(primary_key=True, constraints=[SQL("UNSIGNED")])
    user_id = BigIntegerField(constraints=[SQL("UNSIGNED")], null=False)
    email = CharField(255, null=False)
    role_id = BigIntegerField(constraints=[SQL("UNSIGNED")], null=False)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")], null=False)
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")], null=False)

    class Meta:
        table_name = 'app_user_role'
        indexes = (
            (('user_id', 'role_id'), True),
            (('email', 'role_id'), True),
        )
