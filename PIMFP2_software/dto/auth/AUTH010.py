from dataclasses import dataclass

import msgspec

from ..constraint import Password


@dataclass
class AUTH010Req(msgspec.Struct, rename="camel"):
    reset_token: str
    password: Password
