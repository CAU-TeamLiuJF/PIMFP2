import logging
import flask
from flask import request, g


class RequestContextFilter(logging.Filter):
    """
    A logging filter that adds Flask request and g context information to log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add request and g information if request context available
        """
        record.remote_addr = ""
        record.method = ""
        record.path = ""
        record.endpoint = ""
        record.session_id = ""
        record.request_id = ""
        record.trace_id = ""
        if flask.has_request_context():
            record.remote_addr = request.remote_addr or ""
            record.method = request.method or ""
            record.path = request.path or ""
            record.endpoint = request.endpoint or ""
            record.session_id = g.get("session_id", "")
            record.request_id = g.get("request_id", "")
            record.trace_id = g.get("trace_id", "")

        return True
