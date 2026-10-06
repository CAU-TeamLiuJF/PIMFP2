from dataclasses import dataclass

import msgspec

from ..constraint import Organization


@dataclass
class AUTH012Req(msgspec.Struct, rename="camel"):
    organization: Organization
