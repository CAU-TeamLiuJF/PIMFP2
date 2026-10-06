from peewee import Model
from pimfp.middleware.db import db


class BaseModel(Model):
    class Meta:
        database = db


from pimfp.model.app_user import AppUser
from pimfp.model.app_role import AppRole
from pimfp.model.app_user_role import AppUserRole
from .predict_task import PredictTask
from .daily_quota import DailyQuota
from .image_mapping import ImageMapping

__all__ = [
    "AppUser",
    "AppRole",
    "AppUserRole",
    "PredictTask",
    "DailyQuota",
    "ImageMapping",
]
