from dataclasses import dataclass
from typing import Optional

import msgspec

from ..constraint import Email


@dataclass
class RoleDTO(msgspec.Struct, rename="camel"):
    code: str


@dataclass
class UserDTO(msgspec.Struct, rename="camel"):
    email: Email
    organization: str
    roles: Optional[list[RoleDTO]]
