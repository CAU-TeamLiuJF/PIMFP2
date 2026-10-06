from functools import wraps
from typing import Callable, TypeVar

import msgspec
from flask import request, make_response, g, Response

from pimfp import logger
from pimfp.dto import BizRsp, BizRspHeader
from pimfp.error import BizI18nError, CommonErrCode
from pimfp.helper import server

LOGGER = logger.get_logger(__name__)
T = TypeVar("T")
R = TypeVar("R")


def jsonreq(type: T) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    A decorator factory that validates and deserializes JSON request payloads into a typed object,
    and injecting the object as the first parameter.

    This decorator ensures incoming requests are properly formatted JSON and converts them
    into strongly-typed Python objects.

    Args:
        type: The type to deserialize the JSON into.

    Returns:
        A decorator function that wraps the original endpoint handler, injecting the
        deserialized request object as the first parameter.

    Raises:
        BizI18nError:
            - CommonErrCode.BAD_REQUEST: If request's mimetype is not JSON
            - CommonErrCode.PARAM_ERROR: If request payload is empty or JSON deserialization fails
    """

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> R:
            if not request.is_json:
                LOGGER.error("mimetype is neither 'application/json' nor 'application/*+json'")
                raise BizI18nError(CommonErrCode.BAD_REQUEST)

            if request.data is None:
                LOGGER.error("empty json data")
                raise BizI18nError(CommonErrCode.PARAM_ERROR)

            try:
                req_data = msgspec.json.decode(request.data, type=type)
            except Exception as e:
                LOGGER.error(f"fail to deserialize request json data to {type}", exc_info=e)
                raise BizI18nError(CommonErrCode.PARAM_ERROR)
            return func(req_data, *args, **kwargs)

        return wrapper

    return decorator


def formreq(type: T) -> Callable[[Callable[..., R]], Callable[..., R]]:
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> R:
            if request.mimetype != "multipart/form-data":
                LOGGER.error("mimetype is not 'multipart/form-data'")
                raise BizI18nError(CommonErrCode.BAD_REQUEST)

            if request.form is None:
                LOGGER.error("empty form")
                raise BizI18nError(CommonErrCode.PARAM_ERROR)

            req_data_raw = request.form.get('data')
            if req_data_raw is None:
                LOGGER.error("empty form data")
                raise BizI18nError(CommonErrCode.PARAM_ERROR)

            try:
                req_data = msgspec.json.decode(req_data_raw, type=type)
            except Exception as e:
                LOGGER.error(f"fail to deserialize form.data json to {type}", exc_info=e)
                raise BizI18nError(CommonErrCode.PARAM_ERROR)
            return func(req_data, *args, **kwargs)

        return wrapper

    return decorator


def jsonrsp(func: Callable[..., R]) -> Callable[..., Response]:
    """
    A decorator that serializes handler return values into a JSON Flask Response. The response
    will be injected as the first parameter, allowing the handler to direct manipulate the response
    beyond just the JSON body, such as setting headers or cookies.

    Args:
        func: The endpoint handler function that returns a Python object to be serialized.

    Returns:
        A wrapped function that returns a Flask Response object with JSON-encoded content.
        The original handler's return value is automatically encoded as JSON.
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> Response:
        response = make_response()
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        ret = func(response, *args, **kwargs)
        response.data = msgspec.json.encode(ret) if ret is not None else b""
        return response

    return wrapper


def jsonapi(type: T):
    """
    A convenience decorator factory that combines both request deserialization and response serialization.

    This is a composite decorator that applies both `jsonify_req` and `jsonify_rsp` in the correct order,
    providing a complete JSON API interface. It simplifies the common pattern of accepting JSON requests
    and returning JSON responses, reducing boilerplate code in endpoint definitions.

    Parameter Order:
    The wrapped handler function should accept parameters in this order:
    1. `req_data`: The deserialized request object (type specified by the `type` parameter)
    2. `response`: A Flask Response object for direct response manipulation
    3. Any additional parameters from the Flask (e.g., URL parameters)

    Args:
        type: The type to deserialize the incoming JSON request payloads into.

    Returns:
        A decorator that transforms a handler function into a complete JSON API endpoint.
        The wrapped function will receive the deserialized request object as its first parameter
        and a Flask Response object as its second parameter, with its return value automatically
        serialized to JSON and written into the response.

    Usage:
        @jsonapi(type=RequestDTO)
        def endpoint(req: RequestDTO, response: Response, user_id: int) -> ReturnType:
            # Can manipulate response (headers, status code) before returning
            response.headers['X-Request-ID'] = g.request_id
            # Process request and return data that will be JSON-serialized
            return {'user_id': user_id, 'data': process(req)}
    """

    def decorator(func: Callable[..., R]) -> Callable[..., Response]:
        return jsonrsp(jsonreq(type=type)(func))

    return decorator


def bizrspify(func: Callable[..., R]) -> Callable[..., BizRsp]:
    """
    A decorator that standardizes API responses by wrapping them in a consistent business response format.

    This decorator encapsulates the handler's return value within a `BizRsp` object, which includes
    a standardized header with metadata (request ID, server date, transaction status) and the actual
    response data. It promotes consistency across all API endpoints and separates business logic
    from response formatting concerns.

    Args:
        func: The endpoint handler function that returns business data (or None).

    Returns:
        A wrapped function that returns a `BizRsp` object containing:
            - header: Standardized metadata including request tracking and server information
            - data: The original return value from the business logic function
    """

    @wraps(func)
    def wrapper(*args, **kwargs) -> BizRsp:
        ret = func(*args, **kwargs)
        rsp = BizRsp(
            header=BizRspHeader(
                request_id=g.request_id,
                server_date=server.get_server_date().strftime("%Y-%m-%d"),
                tran_success=True
            )
        )
        if ret is not None:
            rsp.data = ret
        return rsp

    return wrapper
