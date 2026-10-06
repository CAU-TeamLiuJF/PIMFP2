from dataclasses import dataclass

import msgspec

from .auth_dto import UserDTO


@dataclass
class AUTH011Rsp(msgspec.Struct, rename="camel"):
    user: UserDTO
