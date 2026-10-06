from dataclasses import dataclass

import msgspec

from .auth_dto import UserDTO


@dataclass
class AUTH006Req(msgspec.Struct, rename="camel"):
    remember_token: str


@dataclass
class AUTH006Rsp(msgspec.Struct, rename="camel"):
    user: UserDTO
