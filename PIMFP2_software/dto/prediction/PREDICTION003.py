from dataclasses import dataclass

import msgspec


@dataclass
class PREDICTION003Rsp(msgspec.Struct, rename="camel"):
    avail_quota: int
