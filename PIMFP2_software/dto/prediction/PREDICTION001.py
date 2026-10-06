from dataclasses import dataclass

import msgspec


@dataclass
class PREDICTION001Req(msgspec.Struct, rename="camel"):
    flow_no: str
