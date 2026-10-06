import time

import shortuuid
from flask import Flask, request, g, Response
from werkzeug.exceptions import UnsupportedMediaType

from pimfp import logger
from pimfp.entity import SupportedLocaleEnum, SupportedLocaleMap
from .error_hook import _after_catch

_LOGGER = logger.get_logger(__name__)

_X_TRACE_ID = "X-Trace-Id"
_X_LOCALE = "X-Locale"
_X_CLIENT_INFO = "X-Client-Info"


def entry_hook(app: Flask):
    @app.before_request
    def before_request():
        g.request_id = shortuuid.uuid()
        g.start_time = time.monotonic()

        _LOGGER.info(f"==== PIMFP START ==== {request.remote_addr} \"{request.method} {request.path}\"")
        if request.is_json:
            _LOGGER.info(f"PIMFP_RECEIVE:\n{str(request.data, encoding=request.content_encoding or 'UTF-8')}")
        elif request.mimetype == "multipart/form-data":
            _LOGGER.info(f"PIMFP_RECEIVE:\nform:{request.form}\nfiles:{request.files}")
        else:
            raise UnsupportedMediaType

        if request.routing_exception:
            raise request.routing_exception

        # trace_id
        trace_id = request.headers.get(_X_TRACE_ID)
        if trace_id:
            g.trace_id = trace_id
        else:
            _LOGGER.warning(f"trace_id not found")

        # locale
        raw_locale = request.headers.get(_X_LOCALE)
        matched_locale = SupportedLocaleMap.get(raw_locale, SupportedLocaleEnum.EN_US)
        g.locale = matched_locale


    @app.after_request
    @_after_catch
    def after_request(response: Response) -> Response:
        _LOGGER.info(f"耗时: {(time.monotonic() - g.start_time) * 1_000:.3f} ms")
        _LOGGER.info(f"PIMFP_RESPONSE:\n{str(response.data, encoding='UTF-8')}")
        _LOGGER.info(f"==== PIMFP END ==== {request.remote_addr} \"{request.method} {request.path}\" {response.status_code}")
        return response
