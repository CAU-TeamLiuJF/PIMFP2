from peewee import BigAutoField, CharField, DateTimeField, SQL, IntegerField

from pimfp.entity import PredictTaskStatus, PredictionType, UltrasoundType, PigType
from . import BaseModel
from .field import TinyIntEnumField, MediumTextField


class PredictTask(BaseModel):
    id = BigAutoField(primary_key=True, constraints=[SQL("UNSIGNED")])
    flow_no = CharField(32, unique=True, null=False)
    email = CharField(255, null=False)
    prediction_type = TinyIntEnumField(enum_clz=PredictionType, null=False)
    ultrasound_type = TinyIntEnumField(enum_clz=UltrasoundType, null=False)
    pig_type = TinyIntEnumField(enum_clz=PigType, null=False)
    summary = MediumTextField(null=True)
    total_images = IntegerField(null=False, constraints=[SQL("UNSIGNED")])
    uploading_images = IntegerField(default=0, null=False, constraints=[SQL("UNSIGNED DEFAULT 0")])
    uploaded_images = IntegerField(default=0, null=False, constraints=[SQL("UNSIGNED DEFAULT 0")])
    result = MediumTextField(null=True)
    status = TinyIntEnumField(enum_clz=PredictTaskStatus, null=False, default=PredictTaskStatus.INITIAL,
                              constraints=[SQL(f"DEFAULT {PredictTaskStatus.INITIAL.value}")])
    reason = CharField(64, null=True)
    submit_at = DateTimeField(null=False)
    prepared_at = DateTimeField(null=True)
    queue_at = DateTimeField(null=True)
    processing_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    created_at = DateTimeField(null=False, constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(null=False, constraints=[SQL("DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")])

    class Meta:
        table_name = 'predict_task'
