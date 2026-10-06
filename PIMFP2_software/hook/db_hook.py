from flask import Flask
from pimfp.middleware.db import db


def db_hook(app: Flask):
    @app.before_request
    def before_request():
        db.connect()

    @app.teardown_request
    def teardown_request(_):
        if not db.is_closed():
            db.close()
