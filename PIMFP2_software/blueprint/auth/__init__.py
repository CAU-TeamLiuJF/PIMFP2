from flask import Blueprint

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

__all__ = [
    "auth_bp"
]

# register all auth api
from . import route
