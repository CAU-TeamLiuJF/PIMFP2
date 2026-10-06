from peewee import BigAutoField, CharField, DateTimeField, SQL

from . import BaseModel


class ImageMapping(BaseModel):
    id = BigAutoField(primary_key=True, constraints=[SQL("UNSIGNED")])
    flow_no = CharField(32, index=True, null=False)
    filename = CharField(255, null=False)
    local_path = CharField(512, null=False)
    created_at = DateTimeField(null=False, constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(null=False, constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])

    class Meta:
        table_name = 'image_mapping'
        indexes = (
            (('flow_no', 'filename'), True),
        )
