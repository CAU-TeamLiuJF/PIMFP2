from flask import Blueprint

prediction_bp = Blueprint("prediction", __name__, url_prefix="/prediction")

__all__ = [
    "prediction_bp"
]

from . import route
