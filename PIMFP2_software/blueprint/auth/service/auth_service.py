import base64
import secrets
from datetime import datetime
from typing import Optional

import shortuuid
from flask import g
from peewee import IntegrityError

from pimfp import logger
from pimfp.dao import auth_dao
from pimfp.entity import User, SessionStatus
from pimfp.entity import UserStatus, RoleEnum
from pimfp.entity.auth import Role, Session
from pimfp.error import BizI18nError, AuthErrCode
from pimfp.helper import safetool
from pimfp.middleware.i18n import i18n
from pimfp.middleware.redis import redis, Region
from pimfp.middleware.smtp import smtp, EmailAddress
from . import email_service

_LOGGER = logger.get_logger(__name__)


def register_code_key(email: str) -> str:
    return f"{Region.REGISTER.region}::verify_code::{email}"


def login_code_key(email: str) -> str:
    return f"{Region.LOGIN.region}::verify_code::{email}"


def remember_me_key(r_token: str) -> str:
    return f"{Region.REMEMBERME.region}::{r_token}"


def session_key(s_id: str) -> str:
    return f"{Region.SESSION.region}::{s_id}"


def session_status_key(email: str) -> str:
    return f"{Region.SESSION.region}::{email}::session_status"


def reset_code_key(email: str) -> str:
    return f"{Region.RESET.region}::verify_code::{email}"


def reset_token_key(reset_token: str) -> str:
    return f"{Region.RESET.region}::{reset_token}"


def send_register_code(email: str):
    verify_code = email_service.generate_register_code()
    redis.set(
        register_code_key(email),
        verify_code,
        ex=Region.REGISTER.ttl
    )

    mime = email_service.render_register_email(
        verify_code=verify_code,
        expire=5,  # minutes
        rights_year=datetime.now().strftime("%Y"),
        locale=g.locale
    )
    subject = i18n.t("bizmsg", "auth.register.email_subject", g.locale.value)
    smtp.send_email(
        to_addrs=[EmailAddress(email, None)],
        subject=subject,
        content=mime
    )


def check_register_code(email: str, verify_code: str) -> bool:
    return redis.delifeq(register_code_key(email), verify_code)


def register(email: str, password: str, organization: str):
    if auth_dao.exists_email(email):
        raise BizI18nError(AuthErrCode.EMAIL_ALREADY_REGISTERED)

    # register user
    encrypted_pass = base64.b64encode(safetool.bcrypt_hash(password)).decode("ASCII")
    try:
        auth_dao.create_user(email, encrypted_pass, organization)
    except IntegrityError as e:
        _LOGGER.error(f"email already registered:{email}", exc_info=e)
        raise BizI18nError(AuthErrCode.EMAIL_ALREADY_REGISTERED)
    except Exception as e:
        _LOGGER.error(f"failed to register email/user:{email}", exc_info=e)
        raise BizI18nError(AuthErrCode.REGISTER_FAILED)


def authenticate(email: str, password: str) -> Optional[User]:
    app_user = auth_dao.get_user_by_email(email)
    # user not exist
    if app_user is None:
        _LOGGER.warning(f"unknown email/user:{email}, attempts to login")
        raise BizI18nError(AuthErrCode.BAD_EMAIL_PASSWORD)

    # abnormal user
    if app_user.status is UserStatus.DISABLED:
        _LOGGER.warning(f"disallow abnormal email/user:{email} to login")
        raise BizI18nError(AuthErrCode.ABNORMAL_USER)

    # wrong password
    if not safetool.bcrypt_validate(password, base64.b64decode(app_user.password)):
        raise BizI18nError(AuthErrCode.BAD_EMAIL_PASSWORD)

    # only inner user doesn't need two-factor authentication
    roles = auth_dao.query_user_roles_by_email(app_user.email) or []
    if not any(role.code == RoleEnum.INNER.code for role in roles):
        return None

    return User(
        id=app_user.id,
        email=app_user.email,
        organization=app_user.organization,
        status=app_user.status,
        roles=[Role(id=role.id, code=role.code, description=role.description) for role in roles]
    )


def two_factor_authenticate(email: str, password: str, verify_code: str) -> User:
    app_user = auth_dao.get_user_by_email(email)
    # user not exist
    if app_user is None:
        _LOGGER.warning(f"unknown email/user:{email}, attempts to login")
        raise BizI18nError(AuthErrCode.BAD_EMAIL_PASSWORD)

    # wrong password
    if not safetool.bcrypt_validate(password, base64.b64decode(app_user.password)):
        raise BizI18nError(AuthErrCode.BAD_EMAIL_PASSWORD)

    # abnormal user
    if app_user.status != UserStatus.NORMAL:
        _LOGGER.warning(f"disallow abnormal email/user:{email} to login")
        raise BizI18nError(AuthErrCode.ABNORMAL_USER)

    # credential right, then check login code
    if not redis.delifeq(login_code_key(email), verify_code):
        raise BizI18nError(AuthErrCode.BAD_VERIFY_CODE)

    # get user roles
    roles = auth_dao.query_user_roles_by_email(app_user.email)

    return User(
        id=app_user.id,
        email=app_user.email,
        organization=app_user.organization,
        status=app_user.status,
        roles=[Role(id=role.id, code=role.code, description=role.description) for role in roles]
    )


def auto_authenticate(r_token: str) -> User:
    email = redis.get(remember_me_key(r_token), type=str)
    if not email:
        _LOGGER.warning(f"unknown remember token:{r_token}")
        raise BizI18nError(AuthErrCode.BAD_REMEMBER_TOKEN)

    session_status = redis.get(session_status_key(email), type=SessionStatus)
    if not session_status:
        raise BizI18nError(AuthErrCode.BAD_REMEMBER_TOKEN)

    if r_token != session_status.r_token:
        raise BizI18nError(AuthErrCode.BAD_REMEMBER_TOKEN)

    app_user = auth_dao.get_user_by_email(email)
    # user not exist
    if app_user is None:
        _LOGGER.warning(f"unknown email/user:{email}, attempts to auto-login with token:{r_token}")
        raise BizI18nError(AuthErrCode.BAD_REMEMBER_TOKEN)

    # abnormal user
    if app_user.status != UserStatus.NORMAL:
        _LOGGER.warning(f"disallow abnormal email/user:{email} to auto-login")
        raise BizI18nError(AuthErrCode.BAD_REMEMBER_TOKEN)

    # get user roles
    roles = auth_dao.query_user_roles_by_email(app_user.email) or []

    return User(
        id=app_user.id,
        email=app_user.email,
        organization=app_user.organization,
        status=app_user.status,
        roles=[Role(id=role.id, code=role.code, description=role.description) for role in roles]
    )


def send_login_code(email: str):
    app_user = auth_dao.get_user_by_email(email)
    if app_user is None:
        _LOGGER.warning(f"refusing to send login code to unknown email/user: {email}")
        return
    if app_user.status != UserStatus.NORMAL:
        _LOGGER.warning(f"refusing to send login code to abnormal email/user: {email}")
        raise BizI18nError(AuthErrCode.ABNORMAL_USER)

    verify_code = email_service.generate_login_code()
    redis.set(
        login_code_key(email),
        verify_code,
        ex=Region.LOGIN.ttl
    )
    mime = email_service.render_login_email(
        verify_code=verify_code,
        expire=5,  # minutes
        rights_year=datetime.now().strftime("%Y"),
        locale=g.locale
    )
    subject = i18n.t("bizmsg", "auth.login.email_subject", g.locale.value)
    smtp.send_email(
        to_addrs=[EmailAddress(email, None)],
        subject=subject,
        content=mime
    )


def remember_me(email: str) -> str:
    r_token = shortuuid.uuid()
    redis.set(
        name=remember_me_key(r_token),
        value=email,
        ex=Region.REMEMBERME.ttl
    )
    return r_token


def activate_session(app_user: User, r_token: Optional[str] = None) -> str:
    # store the lastest session status which for multi-login detection
    session_id = shortuuid.uuid()
    session_status = SessionStatus(s_id=session_id, r_token=r_token)
    redis.set(session_status_key(app_user.email), session_status)

    # create and mount session upon the `g`
    # `session_hook` will flush the g.session into cache(redis)
    g.session = Session(s_id=session_id, user=app_user)
    g.session_id = session_id

    return session_id


def deactivate_session(email: str, s_id: Optional[str] = None):
    # delete session
    g.session = None
    if s_id:
        redis.delete(session_key(s_id))

    # delete session status
    session_status = redis.getdel(session_status_key(email), type=SessionStatus)

    # delete session
    if session_status and session_status.s_id:
        redis.delete(session_key(session_status.s_id))

    # delete remember me token
    if session_status and session_status.r_token:
        redis.delete(remember_me_key(session_status.r_token))


def send_reset_code(email: str):
    app_user = auth_dao.get_user_by_email(email)
    if app_user is None:
        _LOGGER.warning(f"refusing to send reset code to unknown email/user: {email}")
        return
    if auth_dao.has_role(app_user.email, RoleEnum.INNER.code):
        _LOGGER.warning(f"refusing to send reset code to inner email/user: {email}")
        return
    if app_user.status != UserStatus.NORMAL:
        _LOGGER.warning(f"refusing to send reset code to abnormal email/user: {email}")
        raise BizI18nError(AuthErrCode.ABNORMAL_USER)

    verify_code = email_service.generate_reset_code()
    redis.set(
        reset_code_key(email),
        verify_code,
        ex=Region.RESET.ttl
    )

    mime = email_service.render_reset_email(
        verify_code=verify_code,
        expire=5,  # minutes
        rights_year=datetime.now().strftime("%Y"),
        locale=g.locale
    )
    subject = i18n.t("bizmsg", "auth.reset.email_subject", g.locale.value)
    smtp.send_email(
        to_addrs=[EmailAddress(email, None)],
        subject=subject,
        content=mime
    )


def check_reset_code(email: str, verify_code: str) -> bool:
    return redis.delifeq(reset_code_key(email), verify_code)


def grant_reset_token(email: str) -> str:
    reset_token = secrets.token_urlsafe(32)
    redis.set(
        name=reset_token_key(reset_token),
        value=email,
        ex=Region.RESET.ttl
    )
    return reset_token


def reset_password(reset_token: str, password: str) -> str:
    email = redis.get(reset_token_key(reset_token), type=str)
    if not email:
        _LOGGER.warning(f"unknown reset token:{reset_token}")
        raise BizI18nError(AuthErrCode.BAD_RESET_TOKEN)

    app_user = auth_dao.get_user_by_email(email)
    if app_user is None:
        _LOGGER.warning(f"unknown email/user:{email}, attempts to reset password with token:{reset_token}")
        raise BizI18nError(AuthErrCode.RESET_PASSWORD_FAILED)

    if app_user.status != UserStatus.NORMAL:
        _LOGGER.warning(f"disallow abnormal email/user:{email} to reset password")
        raise BizI18nError(AuthErrCode.ABNORMAL_USER)

    encrypted_pass = base64.b64encode(safetool.bcrypt_hash(password)).decode("ASCII")
    try:
        auth_dao.update_user_password(email, encrypted_pass)
    except Exception as e:
        _LOGGER.error(f"failed to update password for email/user:{email}", exc_info=e)
        raise BizI18nError(AuthErrCode.RESET_PASSWORD_FAILED)

    return email

def make_up_organization(organization: str) -> None:
    auth_dao.update_organization(g.user.email, organization)
