from dataclasses import dataclass

import msgspec


@dataclass
class PREDICTION002Req(msgspec.Struct, rename="camel"):
    flow_no: str


@dataclass
class PREDICTION002Rsp(msgspec.Struct, rename="camel"):
    flow_no: str
