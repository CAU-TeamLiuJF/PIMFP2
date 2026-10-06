from dataclasses import dataclass
from typing import Union

from msgspec import Struct, UnsetType, UNSET

from .auth_dto import UserDTO
from ..constraint import Email, LoginVerifyCode


@dataclass
class AUTH005Req(Struct, rename="camel"):
    email: Email
    password: str
    verify_code: LoginVerifyCode
    remember_me: bool = False


@dataclass
class AUTH005Rsp(Struct, rename="camel"):
    user: UserDTO
    remember_token: Union[str, None, UnsetType] = UNSET
