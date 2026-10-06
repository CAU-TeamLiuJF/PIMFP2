from dataclasses import dataclass

import msgspec


@dataclass
class PREDICTION004Rsp(msgspec.Struct, rename="camel"):
    total: int
