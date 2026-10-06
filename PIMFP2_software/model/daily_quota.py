from peewee import CharField, DateTimeField, SQL, DateField, IntegerField, BigAutoField

from . import BaseModel


class DailyQuota(BaseModel):
    id = BigAutoField(primary_key=True, constraints=[SQL("UNSIGNED")])
    email = CharField(255, null=False)
    quota_date = DateField(null=False)
    used_quota = IntegerField(null=False, constraints=[SQL("UNSIGNED")], default=0)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])

    class Meta:
        table_name = 'daily_quota'
        indexes = (
            (('email', 'quota_date'), True),
        )
