from dataclasses import dataclass

import msgspec

from ..constraint import Email, ResetVerifyCode


@dataclass
class AUTH009Req(msgspec.Struct, rename="camel"):
    email: Email
    verify_code: ResetVerifyCode


@dataclass
class AUTH009Rsp(msgspec.Struct, rename="camel"):
    reset_token: str
