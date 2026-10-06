from dataclasses import dataclass

import msgspec

from ..constraint import Email


@dataclass
class AUTH008Req(msgspec.Struct, rename="camel"):
    email: Email
