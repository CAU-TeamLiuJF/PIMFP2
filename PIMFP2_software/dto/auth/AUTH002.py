from dataclasses import dataclass

import msgspec

from ..constraint import Email, Password, RegisterVerifyCode, Organization


@dataclass
class AUTH002Req(msgspec.Struct, rename="camel"):
    email: Email
    password: str
    verify_code: RegisterVerifyCode
    organization: Organization
