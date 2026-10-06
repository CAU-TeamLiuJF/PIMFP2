from flask import Flask

from .db_hook import db_hook
from .entry_hook import entry_hook
from .error_hook import error_hook
from .session_hook import session_hook


def init_hooks(app: Flask):
    db_hook(app)
    entry_hook(app)
    session_hook(app)
    error_hook(app)
    return app
