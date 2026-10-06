from flask import Flask, session, request, g

from pimfp import logger
from pimfp.entity import Session
from pimfp.entity import SessionStatus
from pimfp.error import AuthErrCode
from pimfp.error import BizI18nError
from pimfp.middleware.redis import Region
from pimfp.middleware.redis import redis
from .error_hook import _after_catch

LOGGER = logger.get_logger(__name__)

PUBLIC_API = [
    "auth.AUTH001",  # register
    "auth.AUTH002",
    "auth.AUTH003",  # login
    "auth.AUTH004",
    "auth.AUTH005",
    "auth.AUTH006",
    "auth.AUTH008",  # reset password
    "auth.AUTH009",
    "auth.AUTH010",
    "prediction.PREDICTION004",
]


def _multi_login_detect(session_entity: Session):
    session_id = session_entity.s_id
    email = session_entity.user.email

    session_status_key = f"{Region.SESSION.region}::{email}::session_status"
    session_status = redis.get(session_status_key, type=SessionStatus)
    if not session_status:
        # if session_status doesn't exist, it means it was deleted by logout or password reset
        # on purpose for session invalidated.
        LOGGER.warning(f"session status not found: {session_status_key}")
        raise BizI18nError(AuthErrCode.SESSION_INVALIDATED)

    if session_id != session_status.s_id:
        # multi-login detected, raise error
        LOGGER.warning(f"detected login on another device, current:{session_id}, latest:{session_status.s_id}")
        raise BizI18nError(AuthErrCode.MULTI_LOGIN_DETECTED)


def _before_request():
    session_id = session.get("session_id")
    if session_id:
        g.session_id = session_id

    if request.endpoint in PUBLIC_API:
        LOGGER.info(f"public endpoint: {request.endpoint}, bypass")
        return

    if not session_id:
        raise BizI18nError(AuthErrCode.NOT_LOGIN)

    # retrieve session data
    session_key = f"{Region.SESSION.region}::{session_id}"
    session_entity = redis.getex(name=session_key, type=Session, ex=Region.SESSION.ttl)
    if not session_entity:
        raise BizI18nError(AuthErrCode.LOGIN_TIMEOUT)
    LOGGER.info(f"session retrieved: {session_entity}")

    # multiple login detection
    _multi_login_detect(session_entity)
    g.session = session_entity
    g.user = session_entity.user


@_after_catch
def _after_request(response):
    if not "session" in g or not g.session:
        return response

    # multiple login detection
    _multi_login_detect(g.session)

    # update session
    redis.set(
        name=f"{Region.SESSION.region}::{g.session.s_id}",
        value=g.session,
        ex=Region.SESSION.ttl
    )

    return response


def session_hook(app: Flask):
    app.before_request(_before_request)
    app.after_request(_after_request)
