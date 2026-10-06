from dataclasses import dataclass
from typing import Union

from msgspec import Struct, UnsetType, UNSET

from .auth_dto import UserDTO
from ..constraint import Email


@dataclass
class AUTH003Req(Struct, rename="camel"):
    email: Email
    password: str
    remember_me: bool = False


@dataclass
class AUTH003Rsp(Struct, rename="camel"):
    user: Union[UserDTO, None, UnsetType] = UNSET
    remember_token: Union[str, None, UnsetType] = UNSET
    two_factor_auth: bool = False
