from flask import session, g, Response

from pimfp import logger
from pimfp.dto import *
from pimfp.error import BizI18nError, AuthErrCode
from pimfp.helper import jsonapi, jsonrsp, bizrspify
from pimfp.helper.ratelimiter import DistributedFixedWindowRateLimiter
from pimfp.middleware.redis import redis
from . import auth_bp
from .service import auth_service

_LOGGER = logger.get_logger(__name__)

register_code_rl = DistributedFixedWindowRateLimiter(
    redis_client=redis,
    window=50 * 1000,  # 50 seconds
    burst=1
)

login_code_rl = DistributedFixedWindowRateLimiter(
    redis_client=redis,
    window=50 * 1000,  # 50 seconds
    burst=1
)

reset_code_rl = DistributedFixedWindowRateLimiter(
    redis_client=redis,
    window=50 * 1000,  # 50 seconds
    burst=1
)


@auth_bp.post("/AUTH001", endpoint="AUTH001")
@jsonapi(type=AUTH001Req)
@bizrspify
def send_register_code(req_data: AUTH001Req, _: Response) -> None:
    email = req_data.email

    # rate limit
    allowed, required_wait = register_code_rl.try_acquire(identifier=auth_service.register_code_key(email))
    if not allowed:
        _LOGGER.warning(f"sending registration verification codes too frequently, required wait: {required_wait}ms")
        raise BizI18nError(AuthErrCode.VERIFY_CODE_RATE_LIMITED)

    # send verification code
    auth_service.send_register_code(email)


@auth_bp.post("/AUTH002", endpoint="AUTH002")
@jsonapi(type=AUTH002Req)
@bizrspify
def register(req_data: AUTH002Req, _: Response) -> None:
    email = req_data.email
    verify_code = req_data.verify_code

    # check verify code
    if not auth_service.check_register_code(email, verify_code):
        raise BizI18nError(AuthErrCode.BAD_VERIFY_CODE)

    auth_service.register(email, req_data.password, req_data.organization)


@auth_bp.post("/AUTH003", endpoint="AUTH003")
@jsonapi(type=AUTH003Req)
@bizrspify
def login(req_data: AUTH003Req, _: Response) -> AUTH003Rsp:
    email = req_data.email
    password = req_data.password

    # authenticate
    app_user = auth_service.authenticate(email, password)

    # need two-factor authentication
    if app_user is None:
        return AUTH003Rsp(two_factor_auth=True)

    # deal with "remember me"
    r_token = None
    if req_data.remember_me:
        r_token = auth_service.remember_me(email)

    # flask will set the session as cookie in the response
    session_id = auth_service.activate_session(app_user, r_token)
    session["session_id"] = session_id

    return AUTH003Rsp(
        user=UserDTO(
            email=app_user.email,
            organization=app_user.organization,
            roles=[RoleDTO(code=role.code) for role in app_user.roles]
        ),
        remember_token=r_token,
        two_factor_auth=False
    )


@auth_bp.post("/AUTH004", endpoint="AUTH004")
@jsonapi(type=AUTH004Req)
@bizrspify
def send_login_code(req_data: AUTH004Req, _: Response) -> None:
    email = req_data.email

    # rate limit
    allowed, required_wait = login_code_rl.try_acquire(identifier=auth_service.login_code_key(email))
    if not allowed:
        _LOGGER.warning(f"sending login verification codes too frequently, required wait: {required_wait}ms")
        raise BizI18nError(AuthErrCode.VERIFY_CODE_RATE_LIMITED)

    # send verification code
    auth_service.send_login_code(email)


@auth_bp.post("/AUTH005", endpoint="AUTH005")
@jsonapi(type=AUTH005Req)
@bizrspify
def two_factor_login(req_data: AUTH005Req, _: Response) -> AUTH005Rsp:
    email = req_data.email
    verify_code = req_data.verify_code

    # pre-check verify code
    if verify_code != redis.get(auth_service.login_code_key(email), type=str):
        raise BizI18nError(AuthErrCode.BAD_VERIFY_CODE)

    # check email and password
    app_user = auth_service.two_factor_authenticate(
        email=email,
        password=req_data.password,
        verify_code=verify_code
    )

    # deal with "remember me"
    r_token = None
    if req_data.remember_me:
        r_token = auth_service.remember_me(email)

    # flask will set the session as cookie in the response
    session_id = auth_service.activate_session(app_user, r_token)
    session["session_id"] = session_id

    return AUTH005Rsp(
        user=UserDTO(
            email=app_user.email,
            organization=app_user.organization,
            roles=[RoleDTO(code=role.code) for role in app_user.roles]
        ),
        remember_token=r_token
    )


@auth_bp.post("/AUTH006", endpoint="AUTH006")
@jsonapi(type=AUTH006Req)
@bizrspify
def auto_login(req_data: AUTH006Req, _: Response) -> AUTH006Rsp:
    r_token = req_data.remember_token

    # check remember token
    app_user = auth_service.auto_authenticate(r_token)

    # flask will set the session as cookie in the response
    session_id = auth_service.activate_session(app_user, r_token)
    session["session_id"] = session_id

    return AUTH006Rsp(user=UserDTO(
        email=app_user.email,
        organization=app_user.organization,
        roles=[RoleDTO(code=role.code) for role in app_user.roles]
    ))


@auth_bp.post("/AUTH007", endpoint="AUTH007")
@jsonrsp
@bizrspify
def logout(_: Response):
    auth_service.deactivate_session(g.session.user.email, g.session.s_id)
    session.clear()


@auth_bp.post("/AUTH008", endpoint="AUTH008")
@jsonapi(type=AUTH008Req)
@bizrspify
def send_reset_code(req_data: AUTH008Req, _: Response) -> None:
    email = req_data.email

    # rate limit
    allowed, required_wait = reset_code_rl.try_acquire(identifier=auth_service.reset_code_key(email))
    if not allowed:
        _LOGGER.warning(f"sending reset verification codes too frequently, required wait: {required_wait}ms")
        raise BizI18nError(AuthErrCode.VERIFY_CODE_RATE_LIMITED)

    # send verification code
    auth_service.send_reset_code(email)


@auth_bp.post("/AUTH009", endpoint="AUTH009")
@jsonapi(type=AUTH009Req)
@bizrspify
def grant_reset_token(req_data: AUTH009Req, _: Response) -> AUTH009Rsp:
    email = req_data.email
    verify_code = req_data.verify_code

    # check verify code
    if not auth_service.check_reset_code(email, verify_code):
        raise BizI18nError(AuthErrCode.BAD_VERIFY_CODE)

    return AUTH009Rsp(reset_token=auth_service.grant_reset_token(email))


@auth_bp.post("/AUTH010", endpoint="AUTH010")
@jsonapi(type=AUTH010Req)
@bizrspify
def reset_password(req_data: AUTH010Req, _: Response) -> None:
    reset_token = req_data.reset_token
    email = auth_service.reset_password(req_data.reset_token, req_data.password)
    _LOGGER.info(f"password reset for {reset_token}:{email} successfully")

    # invalidate auth
    auth_service.deactivate_session(email)
    session.clear()


@auth_bp.post("/AUTH011", endpoint="AUTH011")
@jsonrsp
@bizrspify
def init_session(_: Response) -> AUTH011Rsp:
    app_user = g.user
    return AUTH011Rsp(user=UserDTO(
        email=app_user.email,
        organization=app_user.organization,
        roles=[RoleDTO(code=role.code) for role in app_user.roles]
    ))

@auth_bp.post("/AUTH012", endpoint="AUTH012")
@jsonapi(type=AUTH012Req)
@bizrspify
def make_up_organization(req_data: AUTH012Req, _: Response) -> None:
    organization = req_data.organization
    auth_service.make_up_organization(organization)
