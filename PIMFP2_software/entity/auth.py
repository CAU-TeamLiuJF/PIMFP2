from dataclasses import dataclass
from enum import IntEnum, Enum
from typing import Optional


class UserStatus(IntEnum):
    DISABLED = 0
    NORMAL = 1


class RoleEnum(Enum):
    VIP = ("user::vip", "VIP用户")
    INNER = ("user::inner", "内部用户")

    def __init__(self, code: str, description: str):
        self._code = code
        self._description = description

    @property
    def code(self) -> str:
        return self._code

    @property
    def description(self) -> str:
        return self._description


@dataclass
class Role:
    id: int
    code: str
    description: str


@dataclass
class User:
    id: int
    email: str
    organization: str
    status: int
    roles: list[Role]


@dataclass
class Session:
    s_id: str
    user: User


@dataclass
class SessionStatus:
    s_id: Optional[str] = None
    r_token: Optional[str] = None
