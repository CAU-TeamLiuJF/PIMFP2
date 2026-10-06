from dataclasses import dataclass
from typing import Union, Any

from msgspec import Struct, UnsetType, UNSET


@dataclass
class BizRspHeader(Struct, rename="camel"):
    request_id: str
    tran_success: bool
    server_date: str
    err_code: Union[str, None, UnsetType] = UNSET
    err_msg: Union[Any, None, UnsetType] = UNSET


@dataclass
class BizRsp(Struct, rename="camel"):
    header: BizRspHeader
    data: Union[Any, None, UnsetType] = UNSET
