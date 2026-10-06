from functools import wraps
from typing import Callable

from flask import Flask, g, Response
from werkzeug.exceptions import HTTPException

from pimfp import logger, SupportedLocaleEnum
from pimfp.dto import BizRspHeader, BizRsp
from pimfp.error import BizError, CommonErrCode
from pimfp.error import BizI18nError
from pimfp.helper import jsonrsp, server
from pimfp.middleware.i18n import i18n

_LOGGER = logger.get_logger(__name__)

_ERROR_MSG_DOMAIN = "errmsg"


def _error_handler(e: Exception) -> Response:
    _LOGGER.error("error caught:", exc_info=e)
    return _do_handle_error(e)


@jsonrsp
def _do_handle_error(_: Response, e: Exception) -> BizRsp:
    server_date = server.get_server_date().strftime("%Y-%m-%d")
    if isinstance(e, HTTPException):
        code = str(e.code)
        msg = e.description
    elif isinstance(e, BizError):
        code = e.code
        msg = e.msg
    elif isinstance(e, BizI18nError):
        locale = g.get("locale", SupportedLocaleEnum.EN_US).value
        code = e.code
        msg = i18n.t(_ERROR_MSG_DOMAIN, e.code, locale, *e.args, **e.kwargs)
    else:
        locale = g.get("locale", SupportedLocaleEnum.EN_US).value
        code = CommonErrCode.UNKNOWN_ERROR.code
        msg = i18n.t(_ERROR_MSG_DOMAIN, CommonErrCode.UNKNOWN_ERROR.code, locale)
    return BizRsp(
        header=BizRspHeader(
            request_id=g.request_id,
            server_date=server_date,
            tran_success=False,
            err_code=code,
            err_msg=msg
        )
    )


def error_hook(app: Flask):
    app.register_error_handler(Exception, _error_handler)


def _after_catch(func: Callable[..., Response]) -> Callable[..., Response]:
    """
    A decorator for Flask's @after_request hook that catches exceptions raised within after_request functions.

    Flask's global error handlers do not catch exceptions raised in after_request functions,
    so this decorator provides a try-catch mechanism to handle errors gracefully.
    When an exception occurs, it processes the error using _do_handle_error and ensures
    a proper response is returned.

    Args:
        func: The original after_request function to be wrapped

    Returns:
        A wrapped function that handles exceptions in the after_request hook
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            _LOGGER.error("after_request error caught:", exc_info=e)
            return _do_handle_error(e)

    return wrapper
